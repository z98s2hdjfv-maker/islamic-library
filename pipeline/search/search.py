#!/usr/bin/env python3
"""
search.py - query the library search index (built by build_index.py).

Examples
  search.py "التوكل"                         surface form, all figures
  search.py --root وكل                        every word from root w-k-l (tawakkul, wakil, ...)
  search.py --root وكل --by-author            hit counts per figure / work (cross-connections)
  search.py '"نور محمد"' --author rumi        exact phrase (FTS5 syntax), one figure
  search.py --root جهد --lang ar --attribution secure --limit 50
  search.py --root علم --root ذوق --near 10   both roots within 10 words (FTS5 NEAR)
  search.py --json ...                        machine-readable (for agents)

Rules
  Queries are normalised like the index (harakat stripped, alif/ya/kaf/ta marbuta unified).
  OpenITI duplicates: only each work's primary version unless --all-versions.
  Every hit prints its uid (the corpus ID to cite), attribution and source_type.
  ocr_uncorrected / pdf_textlayer_cleaned text must be checked against the page before quoting.
"""
import argparse, json, os, re, signal, sqlite3, sys
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textnorm import norm, root_query_variants

DEFAULT_DB = os.environ.get("LIBRARY_DB", "search/library.sqlite")


def fts_term(t):
    return '"' + t.replace('"', "") + '"'


def build_match(a):
    parts = []
    if a.query:
        q = norm(a.query)
        # keep user FTS syntax (quotes, OR, NEAR, *) but normalise the Arabic inside
        parts.append("norm : (" + q + ")" if a.raw else "norm : (" + " ".join(fts_term(w) for w in q.split()) + ")")
    roots = []
    for r in a.root or []:
        roots.append("(" + " OR ".join(fts_term(v) for v in root_query_variants(r)) + ")")
    if roots:
        if a.near and len(roots) > 1:
            # NEAR needs plain phrases; expand weak-radical variants via OR of NEAR groups
            groups = [root_query_variants(r) for r in a.root]
            import itertools
            nears = [f"NEAR({' '.join(fts_term(x) for x in combo)}, {a.near})" for combo in itertools.product(*groups)]
            parts.append("roots : (" + " OR ".join(nears) + ")")
        else:
            parts.append("roots : (" + " AND ".join(roots) + ")")
    if not parts:
        sys.exit("give a query and/or --root")
    return " AND ".join(parts)


def kwic(text, a, width=90):
    flat = re.sub(r"\s+", " ", text)
    if a.query:
        key = norm(a.query).replace('"', "").split()
        if key:
            # locate first normalised match in the original by scanning words
            ws = flat.split(" ")
            for i, w in enumerate(ws):
                if norm(w).find(key[0]) >= 0:
                    s = " ".join(ws[max(0, i - 12): i + 14])
                    return ("… " if i > 12 else "") + s + (" …" if i + 14 < len(ws) else "")
    return flat[:width * 2] + ("…" if len(flat) > width * 2 else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?"); ap.add_argument("--root", action="append")
    ap.add_argument("--near", type=int); ap.add_argument("--raw", action="store_true", help="pass FTS5 syntax through")
    ap.add_argument("--author", action="append"); ap.add_argument("--work", action="append")
    ap.add_argument("--lang", choices=["ar", "fa"]); ap.add_argument("--attribution", action="append")
    ap.add_argument("--all-versions", action="store_true"); ap.add_argument("--by-author", action="store_true")
    ap.add_argument("--limit", type=int, default=20); ap.add_argument("--json", action="store_true")
    ap.add_argument("--db", default=DEFAULT_DB)
    a = ap.parse_args()
    if not os.path.exists(a.db):
        sys.exit(f"index not found: {a.db} (download the search-index release asset or run build_index.py)")
    db = sqlite3.connect(a.db)
    where, args = ["fts MATCH ?"], [build_match(a)]
    if not a.all_versions: where.append("u.primary_version = 1")
    for col, vals in (("u.author", a.author), ("u.work_key", a.work), ("u.attribution", a.attribution)):
        if vals: where.append(f"{col} IN ({','.join('?' * len(vals))})"); args += vals
    if a.lang: where.append("u.lang = ?"); args.append(a.lang)
    sql_from = "FROM fts JOIN units u ON u.rowid = fts.rowid WHERE " + " AND ".join(where)
    if a.by_author:
        rows = db.execute(f"SELECT u.author, u.work_key, u.attribution, COUNT(*) {sql_from} GROUP BY u.author, u.work_key ORDER BY u.author, COUNT(*) DESC", args).fetchall()
        if a.json: print(json.dumps([dict(author=r[0], work=r[1], attribution=r[2], hits=r[3]) for r in rows], ensure_ascii=False, indent=1)); return
        tot = {}
        for r in rows: tot[r[0]] = tot.get(r[0], 0) + r[3]
        for au in sorted(tot, key=lambda x: -tot[x]):
            print(f"{au}: {tot[au]}")
            for r in rows:
                if r[0] == au: print(f"    {r[3]:6d}  {r[1]}  [{r[2]}]")
        return
    rows = db.execute(f"SELECT u.uid, u.work_key, u.author, u.lang, u.attribution, u.source_type, u.text {sql_from} ORDER BY rank LIMIT ?", args + [a.limit]).fetchall()
    total = db.execute(f"SELECT COUNT(*) {sql_from}", args).fetchone()[0]
    if a.json:
        print(json.dumps(dict(total=total, hits=[dict(uid=r[0], work=r[1], author=r[2], lang=r[3], attribution=r[4], source_type=r[5], text=r[6]) for r in rows]), ensure_ascii=False, indent=1)); return
    print(f"{total} matching units (showing {len(rows)})\n")
    for r in rows:
        flag = "" if r[5] in ("ganjoor", "openiti", "shamela", "typed") else f" ⚠ {r[5]}"
        print(f"{r[0]}  [{r[2]} · {r[4]}{flag}]\n    {kwic(r[6], a)}\n")


if __name__ == "__main__":
    main()
