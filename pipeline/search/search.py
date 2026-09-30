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
  search.py --root نيه --caliph Umar          hadith narrated by Umar (also Abu Bakr / Uthman / Ali)
  search.py "الاعمال بالنيات" --hadith-only    hadith units only, each hit with its hadith record
  search.py --root صبر --narrator "أبو هريرة" --graded صحيح
  search.py --root رحم --agreed                in both al-Bukhari and Muslim (matched by wording; unverified)
  search.py --parallels urn:hadith:0256Bukhari.Sahih:1   all versions of that hadith across collections
  (v32 citation layer)
  search.py --verse 2:31 --chrono               every passage on / quoting 2:31, oldest author first, no query needed
  search.py --root نور --verse 24:35 --how lemma,heading   root hits inside commentary on the Light verse
  search.py --concept qutb --before 700 --min-level corroborated   the Pole before 700 AH, OCR pages only if corroborated
  search.py --root سمو --after 500 --by-author --chrono   hit counts per figure with death years

Rules
  Queries are normalised like the index (harakat stripped, alif/ya/kaf/ta marbuta unified).
  OpenITI duplicates: only each work's primary version unless --all-versions.
  Every hit prints its uid (the corpus ID to cite), attribution and source_type.
  ocr_uncorrected / pdf_textlayer_cleaned text must be checked against the page before quoting.
  With the v32 citation layer every hit also shows the author's death year, its locator (vol/page/leaf, as in
  the corpus record), its heading, and for OCR pages the collation level (verified > corroborated > partial >
  divergent > unmatched; no_witness = nothing to compare against). --min-level keeps typed texts and drops OCR
  pages below the level (unchecked OCR pages are dropped too).
  v33: OCR pages with a best reading (apparatus/best_reading) are searched by that reading and shown with it,
  marked "best reading (N corrections)"; the uid still cites the page, and --ocr shows the raw OCR instead.
"""
import argparse, json, os, re, signal, sqlite3, sys
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textnorm import norm, root_query_variants

DEFAULT_DB = os.environ.get("LIBRARY_DB", "search/library.sqlite")


def narrator_key(s):
    s = re.sub(r"[^ء-ي ]", " ", norm(s or ""))
    s = re.sub(r"\bابي\b", "ابو", s); s = re.sub(r"\bابا\b", "ابو", s); s = re.sub(r"\bابن\b", "بن", s)
    return " ".join(s.split())


def fts_term(t):
    return '"' + t.replace('"', "") + '"'


LEVELS = ["unmatched", "divergent", "partial", "corroborated", "verified"]
TYPED = ("ganjoor", "openiti", "shamela", "typed")
LOC_FIELDS = ("vol", "part", "page_before", "page", "leaf", "printed_page", "poem_number")
LOC_SQL = "rtrim(" + " || ".join(f"COALESCE('{k}=' || ul.{k} || ' ', '')" for k in LOC_FIELDS) + ")"


def has_table(db, t):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())


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
        if a.verse or a.concept: return None
        sys.exit("give a query, --root, --verse or --concept")
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
    ap.add_argument("--hadith-only", action="store_true"); ap.add_argument("--caliph", choices=["Abu Bakr", "Umar", "Uthman", "Ali"])
    ap.add_argument("--narrator"); ap.add_argument("--graded", help="substring of a grade in the sources, e.g. صحيح or sahih")
    ap.add_argument("--agreed", action="store_true"); ap.add_argument("--max-weakest-rank", type=int,
                    help="only hadith whose weakest LINKED narrator is at or above this Taqrib rank (1-12); not a hadith grade")
    ap.add_argument("--parallels", metavar="HADITH_ID")
    ap.add_argument("--verse", metavar="S:A", help="only passages indexed to this verse (commentary on it or quotation of it)")
    ap.add_argument("--how", help="with --verse: verse,lemma,heading,continues,cited (comma-separated)")
    ap.add_argument("--concept", help="only passages indexed to this concept (see the concepts table, e.g. qutb, nur_muhammadi)")
    ap.add_argument("--min-level", choices=LEVELS, help="OCR pages at or above this collation level; typed texts always kept")
    ap.add_argument("--before", type=int, metavar="AH", help="authors who died in or before this year AH")
    ap.add_argument("--after", type=int, metavar="AH", help="authors who died in or after this year AH")
    ap.add_argument("--chrono", action="store_true", help="order by the author's death year instead of relevance")
    ap.add_argument("--ocr", action="store_true", help="show the raw OCR of OCR pages, not the best reading")
    a = ap.parse_args()
    if not os.path.exists(a.db):
        sys.exit(f"index not found: {a.db} (download the search-index release asset or run build_index.py)")
    db = sqlite3.connect(a.db)
    has_h = has_table(db, "hadith")
    has_c = has_table(db, "work_meta") and has_table(db, "verse_refs") and has_table(db, "heads")
    has_r = has_table(db, "unit_reading")
    if (a.verse or a.concept or a.min_level or a.before is not None or a.after is not None or a.chrono) and not has_c:
        sys.exit("this index has no citation layer (built before v32); download the current search-index asset")
    if a.concept and not db.execute("SELECT 1 FROM concepts WHERE concept = ?", (a.concept,)).fetchone():
        sys.exit("unknown concept; one of: " + ", ".join(r[0] for r in db.execute("SELECT concept FROM concepts ORDER BY area, concept")))
    if a.verse and not re.fullmatch(r"\d{1,3}:\d{1,3}", a.verse): sys.exit("--verse takes sura:aya, e.g. 2:31")
    hflt = a.hadith_only or a.caliph or a.narrator or a.graded or a.agreed or a.max_weakest_rank
    if (hflt or a.parallels) and not has_h:
        sys.exit("this index has no hadith tables (built before v17); download the current search-index asset")
    if a.parallels:
        g = db.execute("SELECT parallel_group FROM hadith WHERE hadith_id=?", (a.parallels,)).fetchone()
        if not g or not g[0]: sys.exit("no parallels recorded for " + a.parallels)
        rows = db.execute("""SELECT h.hadith_id, h.narrator, h.grades, h.weakest_rank_name, u.text FROM hadith h
                             LEFT JOIN hadith_units hu ON hu.hadith_id=h.hadith_id LEFT JOIN units u ON u.uid=hu.uid
                             WHERE h.parallel_group=? GROUP BY h.hadith_id ORDER BY h.hadith_id""", (g[0],)).fetchall()
        if a.json: print(json.dumps([dict(hadith_id=r[0], narrator=r[1], grades=r[2], weakest_linked=r[3], text=r[4]) for r in rows], ensure_ascii=False, indent=1)); return
        print(f"group {g[0]}: {len(rows)} versions (matched by wording; unverified)\n")
        for r in rows: print(f"{r[0]}  [{r[1] or '?'}{' · ' + r[2] if r[2] else ''}]\n    {(r[4] or '')[:160]}\n")
        return
    m = build_match(a)
    where, args = ([], []) if m is None else (["fts MATCH ?"], [m])
    if not a.all_versions: where.append("u.primary_version = 1")
    for col, vals in (("u.author", a.author), ("u.work_key", a.work), ("u.attribution", a.attribution)):
        if vals: where.append(f"{col} IN ({','.join('?' * len(vals))})"); args += vals
    if a.lang: where.append("u.lang = ?"); args.append(a.lang)
    join = ""
    if has_c:
        join += " LEFT JOIN work_meta wm ON wm.work_key = u.work_key LEFT JOIN unit_conf uc ON uc.unit = u.rowid" \
                " LEFT JOIN unit_loc ul ON ul.unit = u.rowid LEFT JOIN heads hd ON hd.head = ul.head"
        if has_r: join += " LEFT JOIN unit_reading ur ON ur.unit = u.rowid"
        if a.verse:
            s_, v_ = map(int, a.verse.split(":"))
            hw = [x for x in (a.how or "").split(",") if x]
            where.append("u.rowid IN (SELECT unit FROM verse_refs WHERE sura = ? AND aya = ?" +
                         (f" AND how IN ({','.join('?' * len(hw))})" if hw else "") + ")"); args += [s_, v_] + hw
        if a.concept:
            where.append("u.rowid IN (SELECT unit FROM concept_refs WHERE concept = ?)"); args.append(a.concept)
        if a.min_level:
            ok = LEVELS[LEVELS.index(a.min_level):]
            where.append(f"(u.source_type IN ({','.join('?' * len(TYPED))}) OR uc.level IN ({','.join('?' * len(ok))}))")
            args += list(TYPED) + ok
        if a.before is not None: where.append("wm.death_ah <= ?"); args.append(a.before)
        if a.after is not None: where.append("wm.death_ah >= ?"); args.append(a.after)
    if has_h:
        join += " LEFT JOIN hadith_units hu ON hu.uid = u.uid LEFT JOIN hadith h ON h.hadith_id = hu.hadith_id"
        if hflt: where.append("h.hadith_id IS NOT NULL")
        if a.caliph: where.append("h.caliph = ?"); args.append(a.caliph)
        if a.narrator: where.append("h.narrator_key = ?"); args.append(narrator_key(a.narrator))
        if a.graded: where.append("h.grades LIKE ?"); args.append(f"%{a.graded}%")
        if a.agreed: where.append("h.agreed_upon = 1")
        if a.max_weakest_rank: where.append("h.weakest_rank <= ?"); args.append(a.max_weakest_rank)
    sql_from = ("FROM units u" if m is None else "FROM fts JOIN units u ON u.rowid = fts.rowid") + join + \
               (" WHERE " + " AND ".join(where) if where else "")
    dcol = "wm.death_ah" if has_c else "NULL"
    if a.by_author:
        rows = db.execute(f"SELECT u.author, u.work_key, u.attribution, COUNT(DISTINCT u.uid), {dcol} {sql_from} GROUP BY u.author, u.work_key ORDER BY u.author, COUNT(*) DESC", args).fetchall()
        if a.json: print(json.dumps([dict(author=r[0], work=r[1], attribution=r[2], hits=r[3], death_ah=r[4]) for r in rows], ensure_ascii=False, indent=1)); return
        tot = {}
        for r in rows: tot[r[0]] = tot.get(r[0], 0) + r[3]
        key = (lambda x: (min((9999 if r[4] is None else r[4]) for r in rows if r[0] == x), x)) if a.chrono else (lambda x: -tot[x])
        for au in sorted(tot, key=key):
            print(f"{au}: {tot[au]}")
            for r in rows:
                if r[0] == au: print(f"    {r[3]:6d}  {r[1]}  [{r[2]}{' · d. ' + str(r[4]) if r[4] else ''}]")
        return
    ccols = f", wm.death_ah, wm.title, uc.level, NULLIF({LOC_SQL}, ''), hd.text, wm.page_note" if has_c else ", NULL, NULL, NULL, NULL, NULL, NULL"
    has_ed = has_h and any(c[1] == "edition_no" for c in db.execute("PRAGMA table_info(hadith)"))
    hcols = (", h.hadith_id, h.narrator, h.caliph, h.grades, h.parallel_collections, h.agreed_upon, h.weakest_rank_name" +
             (", h.edition_no" if has_ed else ", NULL")) if has_h else ""
    order = "COALESCE(wm.death_ah, 9999), u.rowid" if a.chrono else ("rank" if m is not None else "u.rowid")
    vcol, vargs = ", NULL", []
    if a.verse:
        vcol, vargs = ", (SELECT group_concat(DISTINCT how) FROM verse_refs WHERE unit = u.rowid AND sura = ? AND aya = ?)", [s_, v_]
    tcol = "COALESCE(ur.reading, u.text)" if has_r and has_c and not a.ocr else "u.text"
    rcol = ", ur.changes" if has_r and has_c else ", NULL"
    rows = db.execute(f"SELECT u.uid, u.work_key, u.author, u.lang, u.attribution, u.source_type, {tcol}{ccols}{vcol}{hcols}{rcol} {sql_from} "
                      f"GROUP BY u.rowid ORDER BY {order} LIMIT ?", vargs + args + [a.limit]).fetchall()
    total = db.execute(f"SELECT COUNT(DISTINCT u.rowid) {sql_from}", args).fetchone()[0]
    if a.json:
        print(json.dumps(dict(total=total, hits=[dict(uid=r[0], work=r[1], author=r[2], lang=r[3], attribution=r[4], source_type=r[5],
              death_ah=r[7], title=r[8], ocr_level=r[9], loc=r[10], heading=r[11], page_note=r[12],
              **({"verse_how": r[13]} if a.verse else {}), best_reading_changes=r[-1],
              text_is="best_reading" if r[-1] and not a.ocr else "corpus", text=r[6]) for r in rows]),
              ensure_ascii=False, indent=1)); return
    print(f"{total} matching units (showing {len(rows)})\n")
    for r in rows:
        flag = "" if r[5] in TYPED else f" ⚠ {r[5]}" + (f" · {r[9]}" if r[9] else (" · unchecked" if has_c else "")) + \
               (f" · best reading ({r[-1]} corrections)" if r[-1] and not a.ocr else "")
        died = f" · d. {r[7]}" if r[7] else ""
        print(f"{r[0]}  [{r[2]}{died} · {r[4]}{flag}]" + (f"  {a.verse} {r[13]}" if a.verse and r[13] else ""))
        if r[10] or r[11]: print("    @ " + " · ".join(x for x in (r[10], r[11]) if x) + (f"  ({r[12]})" if r[12] else ""))
        print(f"    {kwic(r[6], a)}")
        h = r[14:-1]
        if h and h[0]:
            extra = [h[1] or "narrator ?"] + ([h[2]] if h[2] else []) + ([h[3]] if h[3] else []) + \
                    ([f"in {h[4]} collections"] if h[4] and h[4] > 1 else []) + (["Bukhari+Muslim"] if h[5] else []) + \
                    ([f"weakest linked narrator: {h[6]}"] if h[6] else [])
            ed = f" (printed no. {h[7]})" if len(h) > 7 and h[7] else ""
            print(f"    ↳ {h[0]}{ed} · " + " · ".join(extra))
        print()

if __name__ == "__main__":
    main()
