#!/usr/bin/env python3
"""
ocr_quality.py - triage of the library's uncorrected OCR: which works, and which pages in them, most
need checking against a printed edition (catalogs/secondary_literature.tsv) or the scan itself.

Scope: every work whose works_index.tsv source_type is ocr_uncorrected.
Score per record (0-100): the share of its tokens that look like clean Arabic-script words, i.e. 2-15
letters from the Arabic block after removing diacritics, tatweel and punctuation, with no Latin letters
or digits mixed in. Records with fewer than 8 tokens are not scored (headings, blank leaves).
This is a triage signal, not a measure of accuracy: a clean-looking page can still hold misread letters
(e.g. dotting errors), so "good" means "probably readable", never "verified".

Output:
  reports/ocr_quality_works.tsv   work, records scored, mean score, % of records below 60 (poor), below 80 (fair)
  reports/ocr_quality_worst.tsv   the 25 lowest-scoring records per work, with their locator
Usage: python3 pipeline/verify/ocr_quality.py --repo .
"""
import argparse, csv, gzip, json, os, re, statistics

DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
WORD = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]{2,15}")
PUNCT = re.compile(r"^[\s\.,;:!?()\[\]{}«»\"'“”‘’\-–—_/\\|*#%&@<>،؛؟…]+|[\s\.,;:!?()\[\]{}«»\"'“”‘’\-–—_/\\|*#%&@<>،؛؟…]+$")


def score(text):
    toks = [PUNCT.sub("", t) for t in (text or "").split()]
    toks = [t for t in toks if t]
    if len(toks) < 8: return None
    good = sum(1 for t in toks if WORD.fullmatch(DIAC.sub("", t)))
    return round(100 * good / len(toks), 1)


def locator(r):
    return " ".join(f"{k}={r[k]}" for k in ("vol", "page", "page_before", "leaf", "printed_page") if r.get(k) not in (None, ""))


def main(repo):
    idx = list(csv.DictReader(open(os.path.join(repo, "catalogs/works_index.tsv"), encoding="utf-8"), delimiter="\t"))
    works, worst = [], []
    for w in idx:
        if w["source_type"] != "ocr_uncorrected": continue
        p = os.path.join(repo, w["corpus_path"])
        if not os.path.exists(p): continue
        op = gzip.open if p.endswith(".gz") else open
        rows = []
        with op(p, "rt", encoding="utf-8") as f:
            for l in f:
                r = json.loads(l); s = score(r.get("text") or r.get("text_raw"))
                if s is not None: rows.append((s, r.get("id", ""), locator(r)))
        if not rows: continue
        sc = [s for s, _, _ in rows]
        works.append([w["key"], len(rows), round(statistics.mean(sc), 1),
                      round(100 * sum(s < 60 for s in sc) / len(sc), 1), round(100 * sum(s < 80 for s in sc) / len(sc), 1)])
        for s, rid, loc in sorted(rows)[:25]: worst.append([w["key"], rid, loc, s])
    works.sort(key=lambda x: x[2])
    os.makedirs(os.path.join(repo, "reports"), exist_ok=True)
    with open(os.path.join(repo, "reports/ocr_quality_works.tsv"), "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n")
        c.writerow(["work", "records_scored", "mean_score", "pct_poor_lt60", "pct_fair_lt80"]); c.writerows(works)
    with open(os.path.join(repo, "reports/ocr_quality_worst.tsv"), "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n")
        c.writerow(["work", "record_id", "locator", "score"]); c.writerows(worst)
    for x in works: print(*x, sep="\t")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); main(ap.parse_args().repo)
