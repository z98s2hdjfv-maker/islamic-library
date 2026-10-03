#!/usr/bin/env python3
"""
textsearch.py - v37: phrase search straight over the corpus files, no index needed (works in a sparse clone).

Both the text and the query are normalised the same way before matching: textnorm.norm (diacritics and tatweel
removed; alif, ya, ta marbuta and hamza forms unified) and then every non-letter (punctuation, brackets, digits,
page markers) becomes a space. So "فالكلم: اسم، وفعل" is found by the query "فالكلم اسم وفعل", and a query typed
with or without hamzas or harakat finds the same passages. Each query word may carry a proclitic (و ف ب ل ك)
unless --exact. OCR works can be searched by their best reading (--best-reading, apparatus/best_reading).
It matches words, not roots: for root search use the search index (search.py --root).
v39: reads records whose text is structured (the full Mathnawi: hemistichs inside a dict), and never crashes on an
odd record: it is skipped and reported. A fast pre-check on the raw line (spelling variants and vowel marks allowed)
skips non-matching records before decoding: the whole corpus in about 85 s instead of 4 min; --folder is faster
still. --no-prefilter decodes everything (for checking; results are identical in our tests).

v53: the term bridge. Rumi writes in Persian with his own vocabulary, so an Arabic phrase never reached him. When a
query is one of the Arabic terms of catalogs/term_bridge.tsv (مرآة القلب، عالم الأمر، الملكوت ...), his Persian words
for it (آینه دل، عالم امر، جهان جان ...) are searched too, in the same pass, and the output says so. --no-bridge
turns it off. A master is never recorded as silent before his own language has been searched (START_HERE.md).

  python3 pipeline/search/textsearch.py "فالكلم اسم وفعل" --folder lugha
  python3 pipeline/search/textsearch.py "لا يرد القضاء الا الدعاء" --folder hadith,kalam --limit 20
  python3 pipeline/search/textsearch.py "ليس في الامكان ابدع" --count          # hits per work only
  python3 pipeline/search/textsearch.py "الفطرة" "لا تبديل" "عالم الذر" --folder fitra,tafsir --count
                                     # v41: several phrases in ONE pass and one step: batch your searches
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


def flat(v):
    """any JSON value -> its text: strings joined; lists joined with " / " (hemistichs); dicts by their values
    (the full Mathnawi records hold {"source": {"lang", "edition", "hemistichs": [...]}})."""
    if isinstance(v, str): return v
    if isinstance(v, list): return " / ".join(flat(x) for x in v)
    if isinstance(v, dict):
        if "hemistichs" in v: return flat(v["hemistichs"])
        return " ".join(flat(x) for k, x in v.items() if k not in ("lang", "edition"))
    return ""


VAR = {"ا": "اأإآٱﺍ", "ي": "يىئیےې", "ه": "هةۀەہھ", "و": "وؤۆ", "ك": "كکګ", "ء": "ءأإؤئ"}
GAP = "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640\u200c]*"


def prefilter(words):
    """a fast regex on the raw JSON line, before decoding: the longest query word, letter by letter, allowing any
    spelling variant the normaliser unifies and any vowel marks or tatweel between letters."""
    w = max(words, key=len)
    return re.compile(GAP.join(f"[{re.escape(VAR.get(ch, ch))}]" for ch in w))


def exact_loc(r, pat):
    """v42: the exact page of the match. OpenITI page markers END a page (pages.py), so the record starts on
    page_before + 1 and a match further in is on 1 + the last marker before it."""
    from pages import segments, fmt
    if isinstance(r.get("page_before"), int):
        for v, p, t in segments(r):
            if pat.search(clean(t)): return f"vol={v} page={p}" if v is not None else f"page={p}"
        return f"vol={r.get('vol')} page={r['page_before'] + 1}ff"
    return " ".join(f"{k}={r[k]}" for k in LOC if r.get(k) not in (None, ""))


def text_of(r):
    if r.get("hemistichs"): return flat(r["hemistichs"])
    if "hemistich_1" in r: return f'{r["hemistich_1"]} / {r["hemistich_2"]}'
    return flat(r.get("text")) or flat(r.get("text_raw"))


def load_bridge(repo):
    """Arabic term (cleaned) -> the Persian phrases Rumi uses for it (cleaned word lists)."""
    p = os.path.join(repo, "catalogs/term_bridge.tsv"); out = collections.defaultdict(list)
    if not os.path.exists(p): return out
    for line in list(open(p, encoding="utf-8"))[1:]:
        c = line.rstrip("\n").split("\t")
        if len(c) < 3: continue
        fa = [clean(x).split() for x in c[2].split("|") if clean(x)]
        for ar in c[1].split("|"):
            k = clean(ar)
            if k: out[k] += [f for f in fa if f not in out[k]]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="+", help="one or more phrases; several are searched in ONE pass over the files (v41)")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--folder", help="corpus folders, comma-separated (e.g. kalam,lugha,hadith); default: all")
    ap.add_argument("--work", help="only files whose name contains this (e.g. Tirmidhi, Sibawayhi)")
    ap.add_argument("--exact", action="store_true", help="no proclitics on the query words")
    ap.add_argument("--best-reading", action="store_true", help="search OCR records by their best reading where one exists")
    ap.add_argument("--limit", type=int, default=15, help="passages shown per phrase"); ap.add_argument("--context", type=int, default=120)
    ap.add_argument("--no-prefilter", action="store_true", help="decode every record (slower; for checking)")
    ap.add_argument("--count", action="store_true", help="only counts per work"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-bridge", action="store_true", help="do not add Rumi's Persian words for an Arabic term (v53)")
    a = ap.parse_args()
    qs = [clean(x).split() for x in a.query]
    qs = [q for q in qs if q]
    if not qs: sys.exit("empty query after normalisation")
    pre = "" if a.exact else "[وفبلك]?"
    br = {} if a.no_bridge else load_bridge(a.repo)
    alts = [br.get(" ".join(q), []) for q in qs]          # Persian equivalents of each query, if it is a bridged term
    one = lambda q, pre: " ".join(pre + re.escape(w) for w in q)
    pats = [re.compile(r"(?:^| )(?:" + "|".join([one(q, pre)] + [one(f, "") for f in alts[i]]) + r")(?= |$)") for i, q in enumerate(qs)]
    root = os.path.join(a.repo, "corpus")
    folders = a.folder.split(",") if a.folder else sorted(os.listdir(root))
    files = sorted(p for f in folders for p in glob.glob(os.path.join(root, f, "**", "*.jsonl*"), recursive=True))
    if a.work: files = [p for p in files if a.work.lower() in os.path.basename(p).lower()]
    readings = {}
    if a.best_reading:
        for p in glob.glob(os.path.join(a.repo, "apparatus/best_reading/*.jsonl.gz")):
            for l in gzip.open(p, "rt", encoding="utf-8"):
                r = json.loads(l); readings[r["id"]] = r["reading"]
    hits = [[] for _ in qs]; per = [collections.Counter() for _ in qs]; skipped = collections.Counter()
    prf = re.compile("|".join(f"(?:{prefilter(q).pattern})" for q in qs + [f for fs in alts for f in fs]))
    for p in files:
        wk = os.path.relpath(p, root).replace(os.sep, ".").split(".jsonl")[0]
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as f:
            first = f.readline(); escaped = "\\u06" in first or a.no_prefilter   # escapes or --no-prefilter: no raw pre-check
            for line in ([first] + list(f)) if escaped else __import__("itertools").chain([first], f):
                if not escaped and not prf.search(line): continue
                try:
                    r = json.loads(line); t = clean(readings.get(r.get("id")) or text_of(r))
                except Exception:          # one odd record never stops the search; it is counted and reported
                    skipped[wk] += 1; continue
                for qi, pat in enumerate(pats):
                    m = pat.search(t)
                    if not m: continue
                    per[qi][wk] += 1
                    if not a.count and len(hits[qi]) < a.limit:
                        s0, e0 = max(0, m.start() - a.context), min(len(t), m.end() + a.context)
                        hits[qi].append(dict(id=r.get("id"), work=wk, loc=exact_loc(r, pat),
                                             best_reading=r.get("id") in readings, match=t[s0:e0]))
    if a.json:
        res = [dict(query=" ".join(q), total=sum(per[i].values()), per_work=per[i], hits=hits[i],
                    **({"bridge": [" ".join(f) for f in alts[i]]} if alts[i] else {})) for i, q in enumerate(qs)]
        print(json.dumps(res[0] | {"skipped": skipped} if len(res) == 1 else dict(results=res, skipped=skipped), ensure_ascii=False, indent=1)); return
    for i, q in enumerate(qs):
        if i: print("\n" + "=" * 60)
        print(f'"{" ".join(q)}": {sum(per[i].values())} records in {len(per[i])} works ({len(files)} files searched)')
        if alts[i]: print("  term bridge: also searched as Persian " + "، ".join(" ".join(f) for f in alts[i]) + "  (catalogs/term_bridge.tsv)")
        for wk, n in per[i].most_common(): print(f"  {n:6d}  {wk}")
        for h in hits[i]:
            print(f"\n{h['id']}  [{h['work']}{' · best reading' if h['best_reading'] else ''}]" + (f"  @ {h['loc']}" if h["loc"] else ""))
            print("    … " + h["match"] + " …")
    if skipped: print(f"\n(skipped {sum(skipped.values())} unreadable records in {len(skipped)} files: {', '.join(skipped)})")


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # piping into head etc. ends quietly, not with a traceback
    main()
