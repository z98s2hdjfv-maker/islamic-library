#!/usr/bin/env python3
"""
build_concept_index.py - v30: where each key term of our study occurs, across the collections.

catalogs/concepts.tsv   concept id, English label, area (wilaya / nur / asma / address / path), and its Arabic
                        forms, already in the search normaliser's spelling (pipeline/search/textnorm.py: alif forms
                        to ا, ى to ي, ة to ه), separated by "|", and a note on known ambiguities (e.g. awtad is also the Qur'an's "mountains as pegs").
                        Add a row to add a concept. The Futuhat is held in four versions, so it counts up to four times.
A form matches as a whole word or phrase, optionally after the prefixes و ف ب ل ك.
Output (reports/index/):
  concept_index.tsv.gz    concept, work, record_id, n (occurrences in that passage)
  concept_summary.tsv     concept, label, area, works, passages, the five works that use it most
lookup.py --concept qutb then lists the passages, oldest author first, cited and graded.
Usage: python3 pipeline/index/build_concept_index.py --repo . [--groups ...]
"""
import argparse, collections, csv, glob, gzip, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from textnorm import norm  # noqa: E402

GROUPS = "ibnarabi,nur,wilaya,asma,jilani,sufi_manuals,tafsir_sufi,tafsir,shams,aflaki,ghazali,openiti,critics,hadith,afterlife,grading,modern"


def main(repo, groups):
    cons = list(csv.DictReader(open(os.path.join(repo, "catalogs/concepts.tsv"), encoding="utf-8"), delimiter="\t"))
    pats = {c["concept"]: re.compile(r"(?:^|(?<=\s))[وفبلك]?(?:" + "|".join(re.escape(f) for f in c["arabic_forms"].split("|")) + r")(?=\s|$)")
            for c in cons}
    rows, per = [], collections.defaultdict(collections.Counter)
    for g in groups:
        for p in sorted(glob.glob(os.path.join(repo, "corpus", g, "*.jsonl*")) + glob.glob(os.path.join(repo, "corpus", g, "*", "*.jsonl*"))):
            work = f"{g}.{os.path.basename(p).split('.jsonl')[0]}"
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt", encoding="utf-8") as f:
                for l in f:
                    r = json.loads(l); t = r.get("text") or r.get("text_raw")
                    if not isinstance(t, str) or not t: continue
                    t = " ".join(re.findall(r"[\u0621-\u064A]+", norm(t)))
                    for cid, rx in pats.items():
                        n = len(rx.findall(t))
                        if n: rows.append((cid, work, r.get("id", ""), n)); per[cid][work] += n
        print(g, len(rows), flush=True)
    out = os.path.join(repo, "reports/index"); os.makedirs(out, exist_ok=True)
    with gzip.open(os.path.join(out, "concept_index.tsv.gz"), "wt", encoding="utf-8", compresslevel=9) as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["concept", "work", "record_id", "n"])
        w.writerows(sorted(rows))
    npass = collections.Counter(r[0] for r in rows)
    with open(os.path.join(out, "concept_summary.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["concept", "label", "area", "works", "passages", "top_works"])
        for c in cons:
            cid = c["concept"]
            w.writerow([cid, c["label"], c["area"], len(per[cid]), npass[cid],
                        "; ".join(f"{k} ({v})" for k, v in per[cid].most_common(5))])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--groups", default=GROUPS)
    a = ap.parse_args()
    main(a.repo, [g for g in a.groups.split(",") if os.path.isdir(os.path.join(a.repo, "corpus", g))])
