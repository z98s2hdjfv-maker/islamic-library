#!/usr/bin/env python3
"""
textsearch.py - v37: phrase search straight over the corpus files, no index needed (works in a sparse clone).

Both the text and the query are normalised the same way before matching: textnorm.norm (diacritics and tatweel
removed; alif, ya, ta marbuta and hamza forms unified) and then every non-letter (punctuation, brackets, digits,
page markers) becomes a space. So "فالكلم: اسم، وفعل" is found by the query "فالكلم اسم وفعل", and a query typed
with or without hamzas or harakat finds the same passages. Each query word may carry a proclitic (و ف ب ل ك)
unless --exact. OCR works can be searched by their best reading (--best-reading, apparatus/best_reading).
It matches words, not roots: for root search use the search index (search.py --root).

  python3 pipeline/search/textsearch.py "فالكلم اسم وفعل" --folder lugha
  python3 pipeline/search/textsearch.py "لا يرد القضاء الا الدعاء" --folder hadith,kalam --limit 20
  python3 pipeline/search/textsearch.py "ليس في الامكان ابدع" --count          # hits per work only
  python3 pipeline/search/textsearch.py "الهيولى" --work Qashani --best-reading
Output per hit: record id (the uid to cite), work key, locator (vol/page/leaf as in the record), and the matched
passage in normalised form with context. --json gives the same as data.
"""
import argparse, collections, glob, gzip, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from textnorm import norm  # noqa: E402

NONLETTER = re.compile(r"[^\w]|[\d_]", re.UNICODE)
LOC = ("vol", "part", "page_before", "page", "leaf", "printed_page", "poem_number")


def clean(t):
    return " ".join(NONLETTER.sub(" ", norm(t or "")).split())


def text_of(r):
    if r.get("hemistichs"): return " / ".join(r["hemistichs"])
    if "hemistich_1" in r: return f'{r["hemistich_1"]} / {r["hemistich_2"]}'
    return r.get("text") or r.get("text_raw") or ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query"); ap.add_argument("--repo", default=".")
    ap.add_argument("--folder", help="corpus folders, comma-separated (e.g. kalam,lugha,hadith); default: all")
    ap.add_argument("--work", help="only files whose name contains this (e.g. Tirmidhi, Sibawayhi)")
    ap.add_argument("--exact", action="store_true", help="no proclitics on the query words")
    ap.add_argument("--best-reading", action="store_true", help="search OCR records by their best reading where one exists")
    ap.add_argument("--limit", type=int, default=15); ap.add_argument("--context", type=int, default=120)
    ap.add_argument("--count", action="store_true", help="only counts per work"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    q = clean(a.query).split()
    if not q: sys.exit("empty query after normalisation")
    pre = "" if a.exact else "[وفبلك]?"
    pat = re.compile(r"(?:^| )" + " ".join(pre + re.escape(w) for w in q) + r"(?= |$)")
    root = os.path.join(a.repo, "corpus")
    folders = a.folder.split(",") if a.folder else sorted(os.listdir(root))
    files = sorted(p for f in folders for p in glob.glob(os.path.join(root, f, "**", "*.jsonl*"), recursive=True))
    if a.work: files = [p for p in files if a.work.lower() in os.path.basename(p).lower()]
    readings = {}
    if a.best_reading:
        for p in glob.glob(os.path.join(a.repo, "apparatus/best_reading/*.jsonl.gz")):
            for l in gzip.open(p, "rt", encoding="utf-8"):
                r = json.loads(l); readings[r["id"]] = r["reading"]
    hits, per = [], collections.Counter()
    for p in files:
        wk = os.path.relpath(p, root).replace(os.sep, ".").split(".jsonl")[0]
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line); t = clean(readings.get(r.get("id")) or text_of(r))
                m = pat.search(t)
                if not m: continue
                per[wk] += 1
                if not a.count and len(hits) < a.limit:
                    s0, e0 = max(0, m.start() - a.context), min(len(t), m.end() + a.context)
                    hits.append(dict(id=r.get("id"), work=wk, loc=" ".join(f"{k}={r[k]}" for k in LOC if r.get(k) not in (None, "")),
                                     best_reading=r.get("id") in readings, match=t[s0:e0]))
    if a.json:
        print(json.dumps(dict(query=" ".join(q), total=sum(per.values()), per_work=per, hits=hits), ensure_ascii=False, indent=1)); return
    print(f'"{" ".join(q)}": {sum(per.values())} records in {len(per)} works ({len(files)} files searched)')
    for wk, n in per.most_common(): print(f"  {n:6d}  {wk}")
    for h in hits:
        print(f"\n{h['id']}  [{h['work']}{' · best reading' if h['best_reading'] else ''}]" + (f"  @ {h['loc']}" if h["loc"] else ""))
        print("    … " + h["match"] + " …")


if __name__ == "__main__":
    main()
