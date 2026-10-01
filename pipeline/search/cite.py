#!/usr/bin/env python3
"""
cite.py - v42: the exact volume and page of a phrase inside a record, for citing.

  python3 pipeline/search/cite.py urn:openiti:0463IbnCabdBarr.TamhidMuwatta.JK000585-ara1:p01516 "يكذبه العيان والعقل"
  python3 pipeline/search/cite.py <record_id>               # the record's page span (start to end)
Text and phrase are normalised as in textsearch.py (punctuation, vowels, hamza forms). Pages follow pages.py:
OpenITI page markers mark the END of a page, so the page is 1 + the last marker before the phrase.
For Shamela and OCR records the record's own page / leaf / printed_page is the citation.
"""
import argparse, glob, gzip, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pages import segments, fmt  # noqa: E402
from textsearch import clean  # noqa: E402


def find_record(repo, rid):
    pats = []
    if rid.startswith("urn:openiti:"): pats.append(f"corpus/**/*{'.'.join(rid.split(':')[2].split('.')[:2])}*.jsonl*")
    elif rid.startswith("urn:lib:"):
        fo, book = rid.split(":")[2].split(".", 1); pats.append(f"corpus/{fo}/{book}*.jsonl*")
    pats.append("corpus/**/*.jsonl*")
    for pat in pats:
        for p in glob.glob(os.path.join(repo, pat), recursive=True):
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt", encoding="utf-8") as f:
                for l in f:
                    if rid in l:
                        r = json.loads(l)
                        if r.get("id") == rid: return r
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("record"); ap.add_argument("phrase", nargs="?"); ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    r = find_record(a.repo, a.record)
    if not r: sys.exit("record not found")
    if not r.get("page_before") and r.get("page_before") != 0:
        loc = " ".join(f"{k}={r[k]}" for k in ("vol", "part", "page", "leaf", "printed_page", "poem_number") if r.get(k) not in (None, ""))
        print(f"{a.record}\n  not paginated by OpenITI markers; cite as: {loc or '(no locator in the record)'}"); return
    segs = segments(r)
    if not a.phrase:
        print(f"{a.record}\n  pages {fmt(segs[0][0], segs[0][1])} to {fmt(segs[-1][0], segs[-1][1])} ({len(segs)} page pieces)"); return
    q = clean(a.phrase)
    hits = [(v, p) for v, p, t in segs if q in clean(t)]
    if hits:
        print(f"{a.record}\n  \"{a.phrase}\" is on " + ", ".join(fmt(v, p) for v, p in hits)); return
    whole = " ".join(clean(t) for _, _, t in segs)
    if q in whole:   # runs across a page break
        acc, start = "", None
        for v, p, t in segs:
            acc += " " + clean(t)
            if start is None and q.split()[0] in clean(t): start = (v, p)
            if q in " ".join(acc.split()): print(f"{a.record}\n  \"{a.phrase}\" runs across {fmt(*start) if start else '?'}-{p}"); return
    sys.exit(f"phrase not found in {a.record}")


if __name__ == "__main__":
    import signal; signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
