#!/usr/bin/env python3
"""
Mathnawi batch ingestion (generalised from ingest_pilot.py v0.1.1).

    python3 ingest_mathnawi.py --data ganjoor-data --book 1 --sections 77-83 \
        --frames frames_umar_envoy.json --anchor 77:1=1390 \
        --anchor-note "chained from pilot sh76:17=1389" \
        --out batch.jsonl --report batch_report.json

Same rules as the pilot: byte-exact verse text, only verse text imported,
derived Nicholson numbers marked derived_unverified. Frame/speaker values come
from the --frames file, and its annotation_method (e.g. model_suggested) is
recorded on each record.
"""
import argparse, hashlib, json, subprocess, sys, unicodedata
from pathlib import Path

TEXT_KEYS = ("text", "Text")
POS_KEYS = ("versePosition", "VersePosition", "position", "Position")
ORDER_KEYS = ("vOrder", "VOrder", "order", "Order")
RIGHT, LEFT, COMMENT = 0, 1, 5
POS_NAMES = {"right": 0, "left": 1, "centeredverse1": 2, "centeredverse2": 3,
             "single": 4, "paragraph": -1, "comment": 5}


def pick(d, keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def pos(v):
    p = pick(v, POS_KEYS)
    return POS_NAMES.get(p.lower(), p) if isinstance(p, str) else p


def git_sha(repo):
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def pair_couplets(verses, warnings, section):
    verses = sorted(verses, key=lambda v: pick(v, ORDER_KEYS, 0))
    has_pos = all(pos(v) is not None for v in verses)
    lines = [v for v in verses if not has_pos or pos(v) != COMMENT]
    if not has_pos:
        warnings.append(f"sh{section}: no position codes; paired by alternation")
    out, i = [], 0
    while i < len(lines):
        a = lines[i]; b = lines[i + 1] if i + 1 < len(lines) else None
        if has_pos and pos(a) != RIGHT:
            warnings.append(f"sh{section}: unexpected position {pick(a, POS_KEYS)} at order {pick(a, ORDER_KEYS)}; kept as single line")
            out.append((a, None)); i += 1; continue
        if b is None or (has_pos and pos(b) != LEFT):
            warnings.append(f"sh{section}: unpaired hemistich at order {pick(a, ORDER_KEYS)}")
            out.append((a, None)); i += 1; continue
        out.append((a, b)); i += 2
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--book", type=int, default=1)
    ap.add_argument("--sections", required=True, help="e.g. 77-83")
    ap.add_argument("--frames", required=True)
    ap.add_argument("--anchor", required=True, help="section:couplet=nicholson, e.g. 77:1=1390")
    ap.add_argument("--anchor-note", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    lo, hi = map(int, a.sections.split("-"))
    sc, nich0 = a.anchor.split("=")
    asec, acpl = map(int, sc.split(":")); nich0 = int(nich0)
    fm = json.load(open(a.frames, encoding="utf-8"))
    frames, ann = fm["frames"], fm.get("annotation_method", "unspecified")
    cat = f"poets/moulavi/masnavi/daftar{a.book}"
    repo = Path(a.data); sha = git_sha(repo)
    warnings, ign, ignv, per, recs = [], set(), set(), {}, []

    for s in range(lo, hi + 1):
        raw = (repo / cat / f"sh{s}.json").read_bytes()
        poem = json.loads(raw)
        ign |= {k for k in poem if k not in ("verses", "Verses", "title", "Title")}
        verses = pick(poem, ("verses", "Verses"))
        for v in verses:
            ignv |= {k for k in v if k not in TEXT_KEYS + POS_KEYS + ORDER_KEYS}
        cps = pair_couplets(verses, warnings, s)
        per[s] = {"couplets": len(cps), "sha256": hashlib.sha256(raw).hexdigest(),
                  "title": pick(poem, ("title", "Title"))}
        frame, who, voice, stance = frames[str(s)]
        for n, (x, y) in enumerate(cps, 1):
            h = [pick(x, TEXT_KEYS)] + ([pick(y, TEXT_KEYS)] if y else [])
            for t in h:
                if t != unicodedata.normalize("NFC", t):
                    warnings.append(f"sh{s}:{n} text not NFC-normalised (kept as-is)")
            recs.append({
                "work": "mathnawi", "book": a.book, "unit_type": "bayt",
                "text": {"source": {"lang": "fa", "edition": "ganjoor", "hemistichs": h}},
                "concordance": [{"edition": "ganjoor", "section": s, "line": n, "present": "yes"}],
                "frame": frame,
                "speaker": {"who": who, "voice": voice, "narrator_stance": stance, "level": "section"},
                "annotation": {"method": ann, "status": "unverified", "fields": ["frame", "speaker"]},
                "provenance": {"source": "ganjoor-data", "commit": sha, "file": f"{cat}/sh{s}.json",
                               "method": "imported", "status": "unverified"},
            })

    ai = next(i for i, r in enumerate(recs)
              if r["concordance"][0]["section"] == asec and r["concordance"][0]["line"] == acpl)
    anchor_str = f"ganjoor sh{asec}:{acpl}={nich0}" + (f" ({a.anchor_note})" if a.anchor_note else "")
    for i, r in enumerate(recs):
        n = nich0 + (i - ai)
        r["seq"] = n
        r["id"] = f"urn:sufi:rumi.mathnawi:{a.book}.b{n:04d}"
        r["concordance"].append({"edition": "nicholson_gibb", "number": n,
                                 "present": "derived_unverified", "anchor": anchor_str})

    with open(a.out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rep = {"source_commit": sha, "sections": per, "total_couplets": len(recs),
           "nicholson_range_derived": [recs[0]["seq"], recs[-1]["seq"]], "anchor": anchor_str,
           "frame_map": a.frames, "frame_map_method": ann,
           "ignored_source_keys": sorted(ign), "ignored_verse_keys": sorted(ignv), "warnings": warnings}
    Path(a.report).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(recs)} couplets from {len(per)} sections; derived Nicholson "
          f"{recs[0]['seq']}-{recs[-1]['seq']}; {len(warnings)} warnings; commit {sha}")


if __name__ == "__main__":
    main()
