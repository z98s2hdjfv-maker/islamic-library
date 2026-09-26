#!/usr/bin/env python3
"""
Full Mathnawi ingestion: all six books from ganjoor-data, one JSONL per book.

    python3 ingest_full.py --data ganjoor-data --outdir full \
        --frames 1:frames_pilot.json --frames 1:frames_umar_envoy.json ...

Same rules as ingest_pilot.py / ingest_mathnawi.py: byte-exact verse text,
only verse text imported, pairing by Position ("Right"/"Left"), everything
unverified. Sections with no frame map get frame=null, speaker=null.

Numbering:
  * ganjoor_seq / seq = running couplet number within the book in Ganjoor order
    (exact, always present, monotonic).
  * Nicholson numbers are given ONLY inside anchored ranges (--anchor), as
    ganjoor_seq + offset, marked derived_unverified. Ganjoor's counts differ from
    Nicholson's (e.g. Book 1 has 6 extra couplets before sh42), so a plain
    sequential count is NOT a Nicholson number.
  * id: anchored -> urn:sufi:rumi.mathnawi:<book>.b<nicholson>  (as in the batches)
        otherwise -> urn:sufi:rumi.mathnawi:<book>.g<ganjoor_seq> (g = Ganjoor-based)
"""
import argparse, hashlib, json, re, subprocess, unicodedata
from pathlib import Path

TEXT_KEYS = ("text", "Text"); POS_KEYS = ("Position", "position", "VersePosition", "versePosition")
ORDER_KEYS = ("VOrder", "vOrder", "Order", "order")
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


def pair(verses, warnings, tag):
    verses = sorted(verses, key=lambda v: pick(v, ORDER_KEYS, 0))
    lines = [v for v in verses if pos(v) != 5]
    out, i = [], 0
    while i < len(lines):
        a = lines[i]; b = lines[i + 1] if i + 1 < len(lines) else None
        if pos(a) != 0 or b is None or pos(b) != 1:
            warnings.append(f"{tag}: unpaired/unexpected hemistich at order {pick(a, ORDER_KEYS)} "
                            f"(position {pick(a, POS_KEYS)}); kept as single-line record")
            out.append((a, None)); i += 1; continue
        out.append((a, b)); i += 2
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--outdir", default="full")
    ap.add_argument("--frames", action="append", default=[], help="BOOK:path.json (repeatable)")
    ap.add_argument("--anchor", action="append", default=[],
                    help="BOOK:SECFROM-SECTO:OFFSET:NOTE  (nicholson = ganjoor_seq + OFFSET)")
    a = ap.parse_args()
    repo = Path(a.data); out = Path(a.outdir); out.mkdir(exist_ok=True)
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

    fmaps = {}
    for spec in a.frames:
        b, p = spec.split(":", 1)
        fm = json.load(open(p, encoding="utf-8"))
        for s, v in fm["frames"].items():
            fmaps[(int(b), int(s))] = (v, fm.get("annotation_method", "unspecified"), Path(p).name)

    anchors = []
    for spec in a.anchor:
        b, rng, off, note = spec.split(":", 3)
        lo, hi = map(int, rng.split("-"))
        anchors.append((int(b), lo, hi, int(off), note))

    summary = {"source": "ganjoor-data", "commit": sha, "books": {}}
    for book in range(1, 7):
        cat = f"poets/moulavi/masnavi/daftar{book}"
        secs = sorted(int(re.findall(r"\d+", f.name)[0]) for f in (repo / cat).glob("sh*.json"))
        warnings, ign, ignv, per, n_seq = [], set(), set(), {}, 0
        fout = open(out / f"mathnawi_book{book}.jsonl", "w", encoding="utf-8")
        for s in secs:
            raw = (repo / cat / f"sh{s}.json").read_bytes(); poem = json.loads(raw)
            ign |= {k for k in poem if k not in ("Verses", "verses", "Title", "title")}
            verses = pick(poem, ("Verses", "verses"))
            for v in verses:
                ignv |= {k for k in v if k not in TEXT_KEYS + POS_KEYS + ORDER_KEYS}
            cps = pair(verses, warnings, f"book{book} sh{s}")
            fm = fmaps.get((book, s))
            per[s] = {"couplets": len(cps), "first_seq": n_seq + 1, "last_seq": n_seq + len(cps),
                      "sha256": hashlib.sha256(raw).hexdigest(), "title": pick(poem, ("Title", "title")),
                      "frame_map": fm[2] if fm else None}
            for n, (x, y) in enumerate(cps, 1):
                n_seq += 1
                h = [pick(x, TEXT_KEYS)] + ([pick(y, TEXT_KEYS)] if y else [])
                if any(t != unicodedata.normalize("NFC", t) for t in h):
                    warnings.append(f"book{book} sh{s}:{n} text not NFC-normalised (kept as-is)")
                if fm:
                    (frame, who, voice, stance), meth, _ = fm
                    frame_v = frame
                    spk = {"who": who, "voice": voice, "narrator_stance": stance, "level": "section"}
                    ann = {"method": meth, "status": "unverified", "fields": ["frame", "speaker"]}
                else:
                    frame_v, spk, ann = None, None, {"method": "none", "status": "pending", "fields": []}
                anc = next((x for x in anchors if x[0] == book and x[1] <= s <= x[2]), None)
                conc = [{"edition": "ganjoor", "section": s, "line": n, "present": "yes"}]
                if anc:
                    nich = n_seq + anc[3]
                    conc.append({"edition": "nicholson_gibb", "number": nich,
                                 "present": "derived_unverified", "anchor": anc[4]})
                    rid = f"urn:sufi:rumi.mathnawi:{book}.b{nich:04d}"
                else:
                    conc.append({"edition": "nicholson_gibb", "number": None, "present": "unanchored"})
                    rid = f"urn:sufi:rumi.mathnawi:{book}.g{n_seq:04d}"
                rec = {
                    "work": "mathnawi", "book": book, "unit_type": "bayt",
                    "text": {"source": {"lang": "fa", "edition": "ganjoor", "hemistichs": h}},
                    "concordance": conc,
                    "frame": frame_v, "speaker": spk, "annotation": ann,
                    "provenance": {"source": "ganjoor-data", "commit": sha, "file": f"{cat}/sh{s}.json",
                                   "method": "imported", "status": "unverified"},
                    "ganjoor_seq": n_seq, "seq": n_seq,
                    "id": rid,
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fout.close()
        rep = {"book": book, "commit": sha, "sections": len(secs), "total_couplets": n_seq,
               "ignored_source_keys": sorted(ign), "ignored_verse_keys": sorted(ignv),
               "warnings": warnings, "per_section": per}
        (out / f"mathnawi_book{book}_report.json").write_text(
            json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["books"][book] = {"sections": len(secs), "couplets": n_seq, "warnings": len(warnings),
                                  "annotated_sections": sum(1 for s in secs if (book, s) in fmaps)}
        print(book, summary["books"][book])
    (out / "mathnawi_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
