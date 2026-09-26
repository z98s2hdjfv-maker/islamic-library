#!/usr/bin/env python3
"""
Mathnawi pilot ingestion: Book 1, Ganjoor sections 42-76 (lion and hare).

Source: ganjoor-data (https://github.com/ganjoor/ganjoor-data), a git-tracked
export of Ganjoor's poetry content. Work from a local clone pinned to a commit:

    git clone https://github.com/ganjoor/ganjoor-data.git
    git -C ganjoor-data rev-parse HEAD      # record this sha
    python3 ingest_pilot.py --data ganjoor-data --out pilot_lion_hare.jsonl

Output: one JSON record per couplet (spec v0.1 core fields), plus a report.
Rules enforced here (from the spec):
  * verse text is copied byte-exact from the source file; nothing is retyped
  * only verse text is ingested; every other key is logged, never imported
  * Nicholson numbers are DERIVED from one anchor and marked unverified
  * all annotations start as model_suggested / unverified

v0.1.1 patch: ganjoor-data serialises Position as a string enum
("Right", "Left", ...) rather than an int; normalise both forms.
Verse-level keys (incl. AI-generated CoupletSummary) are also logged as ignored.
"""
import argparse, hashlib, json, subprocess, sys, unicodedata
from pathlib import Path

BOOK = 1
SECTIONS = range(42, 77)                      # Ganjoor sh42..sh76 inclusive
CAT_PATH = "poets/moulavi/masnavi/daftar1"

# Anchor for derived Nicholson numbering: Ganjoor sh45, couplet 1 = Nicholson 1.912
ANCHOR_SECTION, ANCHOR_COUPLET, ANCHOR_NICHOLSON = 45, 1, 912

F = "lion_and_hare"
FRAMES = {
    42: ([F, "debate"], "beasts", "character", "rejects"),
    43: ([F, "debate"], "lion", "character", "endorses"),
    44: ([F, "debate"], "beasts", "character", "rejects"),
    45: ([F, "debate"], "lion", "character", "endorses"),
    46: ([F, "debate"], "beasts", "character", "rejects"),
    47: ([F, "debate"], "lion", "character", "endorses"),
    48: ([F, "debate"], "beasts", "character", "rejects"),
    49: ([F, "debate", "azrael_and_solomon"], "narrator", "narrator", "unresolved"),
    50: ([F, "debate"], "lion", "character", "endorses"),
    51: ([F, "debate"], "narrator", "narrator", "verdict_for_lion"),
    52: ([F, "hare_plan"], "beasts", "character", "rejects"),
    53: ([F, "hare_plan"], "hare", "character", "endorses"),
    54: ([F, "hare_plan"], "beasts", "character", "rejects"),
    55: ([F, "hare_plan"], "hare", "character", "endorses"),
    56: ([F, "hare_plan", "digression_knowledge"], "narrator", "narrator", "author"),
    57: ([F, "hare_plan"], "beasts", "character", "silent"),
    58: ([F, "hare_plan"], "hare", "character", "endorses"),
    59: ([F, "hare_ruse"], "mixed", "blended", "silent"),
    60: ([F, "hare_ruse", "digression_fly"], "narrator", "narrator", "author"),
    61: ([F, "hare_ruse"], "lion", "character", "silent"),
    62: ([F, "hare_ruse", "digression_reason"], "narrator", "narrator", "author"),
    63: ([F, "hare_ruse"], "mixed", "blended", "silent"),
    64: ([F, "hare_ruse"], "hare", "character", "approves_ruse"),
    65: ([F, "hare_ruse"], "lion", "character", "silent"),
    66: ([F, "hare_ruse", "hoopoe_and_solomon"], "mixed", "blended", "silent"),
    67: ([F, "hare_ruse", "hoopoe_and_solomon"], "crow", "character", "rejects"),
    68: ([F, "hare_ruse", "hoopoe_and_solomon"], "hoopoe", "character", "endorses"),
    69: ([F, "hare_ruse", "hoopoe_and_solomon", "adam_and_qada"], "hoopoe", "blended", "endorses"),
    70: ([F, "hare_ruse"], "hare", "character", "silent"),
    71: ([F, "hare_ruse"], "hare", "character", "silent"),
    72: ([F, "hare_ruse"], "narrator", "narrator", "author"),
    73: ([F, "resolution"], "hare", "character", "silent"),
    74: ([F, "resolution"], "beasts", "character", "silent"),
    75: ([F, "resolution"], "hare", "blended", "endorses"),
    76: ([F, "digression_greater_jihad"], "narrator", "narrator", "author"),
}

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
    if isinstance(p, str):
        return POS_NAMES.get(p.lower(), p)
    return p


def git_sha(repo: Path):
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def find_verses(poem: dict):
    for k in ("verses", "Verses"):
        if isinstance(poem.get(k), list):
            return poem[k]
    raise KeyError("no verses array found; keys: %s" % sorted(poem))


def pair_couplets(verses, warnings, section):
    verses = sorted(verses, key=lambda v: pick(v, ORDER_KEYS, 0))
    has_pos = all(pos(v) is not None for v in verses)
    lines = [v for v in verses if not has_pos or pos(v) != COMMENT]
    if not has_pos:
        warnings.append(f"sh{section}: no position codes; paired by alternation")
    couplets, i = [], 0
    while i < len(lines):
        a = lines[i]
        b = lines[i + 1] if i + 1 < len(lines) else None
        if has_pos and pos(a) != RIGHT:
            warnings.append(f"sh{section}: unexpected position {pick(a, POS_KEYS)} "
                            f"at order {pick(a, ORDER_KEYS)}; kept as single line")
            couplets.append((a, None)); i += 1; continue
        if b is None or (has_pos and pos(b) != LEFT):
            warnings.append(f"sh{section}: unpaired hemistich at order {pick(a, ORDER_KEYS)}")
            couplets.append((a, None)); i += 1; continue
        couplets.append((a, b)); i += 2
    return couplets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="pilot_lion_hare.jsonl")
    ap.add_argument("--report", default="pilot_report.json")
    args = ap.parse_args()

    repo = Path(args.data)
    sha = git_sha(repo)
    warnings, ignored_keys, ignored_verse_keys, per_section, records = [], set(), set(), {}, []

    for s in SECTIONS:
        path = repo / CAT_PATH / f"sh{s}.json"
        raw = path.read_bytes()
        poem = json.loads(raw)
        ignored_keys |= {k for k in poem if k not in ("verses", "Verses", "title", "Title")}
        verses = find_verses(poem)
        for v in verses:
            ignored_verse_keys |= {k for k in v if k not in TEXT_KEYS + POS_KEYS + ORDER_KEYS}
        couplets = pair_couplets(verses, warnings, s)
        per_section[s] = {"couplets": len(couplets),
                          "sha256": hashlib.sha256(raw).hexdigest(),
                          "title": pick(poem, ("title", "Title"))}
        frame, speaker, voice, stance = FRAMES[s]
        for n, (a, b) in enumerate(couplets, 1):
            h = [pick(a, TEXT_KEYS)] + ([pick(b, TEXT_KEYS)] if b else [])
            for t in h:
                if t != unicodedata.normalize("NFC", t):
                    warnings.append(f"sh{s}:{n} text not NFC-normalised (kept as-is)")
            records.append({
                "work": "mathnawi", "book": BOOK, "unit_type": "bayt",
                "text": {"source": {"lang": "fa", "edition": "ganjoor", "hemistichs": h}},
                "concordance": [{"edition": "ganjoor", "section": s, "line": n, "present": "yes"}],
                "frame": frame,
                "speaker": {"who": speaker, "voice": voice,
                            "narrator_stance": stance, "level": "section"},
                "provenance": {"source": "ganjoor-data", "commit": sha,
                               "file": f"{CAT_PATH}/sh{s}.json",
                               "method": "imported", "status": "unverified"},
            })

    anchor_idx = next(i for i, r in enumerate(records)
                      if r["concordance"][0]["section"] == ANCHOR_SECTION
                      and r["concordance"][0]["line"] == ANCHOR_COUPLET)
    for i, r in enumerate(records):
        nich = ANCHOR_NICHOLSON + (i - anchor_idx)
        r["seq"] = nich
        r["id"] = f"urn:sufi:rumi.mathnawi:{BOOK}.b{nich:04d}"
        r["concordance"].append({"edition": "nicholson_gibb", "number": nich,
                                 "present": "derived_unverified",
                                 "anchor": f"ganjoor sh{ANCHOR_SECTION}:{ANCHOR_COUPLET}={ANCHOR_NICHOLSON}"})

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    report = {"source_commit": sha, "sections": per_section,
              "total_couplets": len(records),
              "nicholson_range_derived": [records[0]["seq"], records[-1]["seq"]],
              "ignored_source_keys": sorted(ignored_keys),
              "ignored_verse_keys": sorted(ignored_verse_keys),
              "warnings": warnings}
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(records)} couplets from {len(per_section)} sections; "
          f"derived Nicholson {records[0]['seq']}-{records[-1]['seq']}; "
          f"{len(warnings)} warnings; commit {sha or 'UNKNOWN - record it!'}")
    if sha is None:
        print("WARNING: not a git clone; record the snapshot commit by hand.", file=sys.stderr)


if __name__ == "__main__":
    main()
