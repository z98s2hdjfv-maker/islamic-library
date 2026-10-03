#!/usr/bin/env python3
"""
cite.py - v42: the exact volume and page of a phrase inside a record, for citing.

  python3 pipeline/search/cite.py urn:openiti:0463IbnCabdBarr.TamhidMuwatta.JK000585-ara1:p01516 "يكذبه العيان والعقل"
  python3 pipeline/search/cite.py <record_id>               # the record's page span (start to end)
Text and phrase are normalised as in textsearch.py (punctuation, vowels, hamza forms). Pages follow pages.py:
OpenITI page markers mark the END of a page, so the page is 1 + the last marker before the phrase.
For Shamela and OCR records the record's own page / leaf / printed_page is the citation.
v53: a hadith-layer id (urn:hadith:<collection>:<number>) resolves to its source paragraph and page, with its printed
number; Shamela, Sufi and Mathnawi ids go straight to their file (a second or two, not fifteen); and several ids can
be resolved in one call:
  python3 pipeline/search/cite.py --many urn:hadith:0261Muslim.Sahih:121.1 urn:shamela:ghazali.ihya_with_iraqi:r01491 ...
"""
import argparse, glob, gzip, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pages import segments, fmt  # noqa: E402
from textsearch import clean  # noqa: E402


def hadith_record(repo, rid):
    """v53: a hadith-layer id -> its layer record (or None)"""
    p = os.path.join(repo, "apparatus/hadith", rid.split(":")[2] + ".jsonl.gz")
    if not os.path.exists(p): return None
    key = json.dumps(rid, ensure_ascii=False)
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for l in f:
            if key in l:
                r = json.loads(l)
                if r.get("id") == rid: return r
    return None


def find_record(repo, rid):
    pats = []
    if rid.startswith("urn:openiti:"): pats.append(f"corpus/**/*{'.'.join(rid.split(':')[2].split('.')[:2])}*.jsonl*")
    elif rid.startswith(("urn:lib:", "urn:shamela:")):
        fo, book = rid.split(":")[2].split(".", 1); pats.append(f"corpus/{fo}/{book}*.jsonl*")
    elif rid.startswith("urn:sufi:rumi.mathnawi:"): pats.append("corpus/mathnawi/full/*.jsonl")
    elif rid.startswith("urn:sufi:"):
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


def one(repo, rid, phrase):
    """resolve one id and print its citation; returns False when it is not found"""
    a = argparse.Namespace(record=rid, phrase=phrase, repo=repo)
    if rid.startswith("urn:hadith:"):
        h = hadith_record(repo, rid)
        if not h: print(f"{rid}\n  not found in the hadith layer"); return False
        pn = "; ".join(f"{x['edition']}: {x['number']}" for x in h.get("edition_numbers") or [])
        src = (h.get("source_ids") or [None])[0]
        print(f"{rid}\n  hadith no. {h.get('number')} ({h.get('numbering')} numbering){'; printed ' + pn if pn else ''}; source paragraph: {src}")
        if not src: return True
        a.record = src
    r = find_record(a.repo, a.record)
    if not r:
        print(f"{a.record}\n  record not found"); return False
    if r.get("hemistichs") or isinstance(r.get("text"), dict):          # a couplet: cite by its number
        nic = next((c.get("number") for c in r.get("concordance", []) if c.get("edition", "").startswith("nicholson")), None)
        loc = f"book {r.get('book')}, couplet {nic} (Nicholson)" if nic else " ".join(f"{k}={r[k]}" for k in ("part", "poem_number", "seq") if r.get(k) not in (None, ""))
        print(f"{a.record}\n  verse; cite as: {loc}"); return True
    if not r.get("page_before") and r.get("page_before") != 0:
        loc = " ".join(f"{k}={r[k]}" for k in ("vol", "part", "page", "leaf", "printed_page", "poem_number") if r.get(k) not in (None, ""))
        print(f"{a.record}\n  not paginated by OpenITI markers; cite as: {loc or '(no locator in the record)'}"); return True
    segs = segments(r)
    if not a.phrase:
        print(f"{a.record}\n  pages {fmt(segs[0][0], segs[0][1])} to {fmt(segs[-1][0], segs[-1][1])} ({len(segs)} page pieces)"); return True
    q = clean(a.phrase)
    hits = [(v, p) for v, p, t in segs if q in clean(t)]
    if hits:
        print(f"{a.record}\n  \"{a.phrase}\" is on " + ", ".join(fmt(v, p) for v, p in hits)); return True
    whole = " ".join(clean(t) for _, _, t in segs)
    if q in whole:   # runs across a page break
        acc, start = "", None
        for v, p, t in segs:
            acc += " " + clean(t)
            if start is None and q.split()[0] in clean(t): start = (v, p)
            if q in " ".join(acc.split()): print(f"{a.record}\n  \"{a.phrase}\" runs across {fmt(*start) if start else '?'}-{p}"); return True
    print(f"phrase not found in {a.record}"); return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record", nargs="?"); ap.add_argument("phrase", nargs="?"); ap.add_argument("--repo", default=".")
    ap.add_argument("--many", nargs="+", metavar="ID", help="resolve several record ids in one call (v53)")
    a = ap.parse_args()
    if a.many:
        ok = [one(a.repo, rid, None) for rid in a.many]
        sys.exit(0 if all(ok) else 1)
    if not a.record: ap.error("give a record id, or --many id id ...")
    if not one(a.repo, a.record, a.phrase): sys.exit("record not found")


if __name__ == "__main__":
    import signal; signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
