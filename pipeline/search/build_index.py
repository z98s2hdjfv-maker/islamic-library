#!/usr/bin/env python3
"""
build_index.py - build the library's search layer: one SQLite file with a full-text index
(FTS5) over every corpus unit, searchable by surface form or by Arabic root.

  units   one row per corpus unit (couplet, paragraph, page): uid, work_key, author, lang,
          attribution, source_type, primary_version, text (as in corpus)
  fts     FTS5 over two columns: norm (normalised surface text) and roots (CAMeL roots)
  works   one row per work with counts, so queries can group by figure/work
  vocab   word type -> CAMeL roots (all analyses, undisambiguated) and frequency
  meta    build facts (repo commit, CAMeL db, counts)
  hadith, hadith_units  (v17) one row per hadith from apparatus/hadith + apparatus/hadith_links, joined
          to units by uid: narrator, caliph, grades found in the sources, parallel group, agreed_upon,
          weakest linked narrator rank (Taqrib) - see add_hadith_tables()
  v32 citation layer - see add_citation_tables(); if it fails, the index is still built without it:
  (the new tables key passages by `unit` = units.rowid, which keeps them small)
  unit_loc      unit -> vol, part, page_before, page, leaf, printed_page, poem_number (as in the corpus record),
                head -> heads.text (last heading)
  work_meta     one row per work: title, death_ah, source_type, witnesses, corroborated/checked pages,
                secondary references, page note (reports/index/works_meta.tsv; OpenITI death year from the name)
  unit_conf     unit -> collation level of OCR pages (reports/collation/confidence.tsv.gz)
  verse_refs    unit -> sura, aya, how (verse/lemma/heading/continues/cited) (reports/index/verse_index.tsv.gz)
  concept_refs  unit -> concept, n; concepts: label, area (reports/index/concept_*.tsv*)
  works         now also carries title, death_ah, witnesses, corroborated, checked, refs, page_note

Roots: every distinct word type is analysed once with CAMeL Tools (morphology-db-msa-r13,
no backoff); the union of roots over all analyses is stored, so root search favours recall.
Persian texts are analysed too (after ی->ي, ک->ك) - this catches Arabic loanwords such as
توکل, but Persian words can pick up spurious Arabic roots; filter with --lang when it matters.

Skips corpus/mathnawi/full/ (same couplets as corpus/mathnawi/book*.tsv, which carry the
Nicholson IDs). OpenITI: all versions are indexed; primary_version=1 marks the catalog's
primary one (search.py uses only primary versions unless --all-versions).

Usage: python3 pipeline/search/build_index.py --repo . --out search/library.sqlite
       ... --only tafsir,ibnarabi.fusus      sample build (work keys / corpus paths containing these), for testing
       ... --add-citations --out FILE        add or refresh the v32 citation layer in an existing index, no rebuild
Needs: pip install camel-tools ; camel_data -i morphology-db-msa-r13
"""
import argparse, csv, glob, gzip, json, os, sqlite3, subprocess, sys, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textnorm import norm, words, root_token

SKIP_ROOTS = {"PUNC", "DIGIT", "FOREIGN", "NTWS", "LATIN", "NOAN"}
OPENITI_AUTHOR = {"0505Ghazali": "ghazali", "0561CabdQadirJilani": "jilani", "0638IbnCarabi": "ibnarabi"}
PERSIAN_AUTHORS = {"shams", "aflaki"}


LOC_DDL = """CREATE TABLE unit_loc(unit INTEGER PRIMARY KEY, vol, part, page_before, page, leaf, printed_page, poem_number, head INT);
             CREATE TABLE heads(head INTEGER PRIMARY KEY, text TEXT);"""


def head_id(heads, h):
    if not h: return None
    i = heads.get(h)
    if i is None: i = heads[h] = len(heads) + 1
    return i


LOC_FIELDS = ("vol", "part", "page_before", "page", "leaf", "printed_page", "poem_number")


def _compact(v):
    if v in (None, ""): return None
    if isinstance(v, str) and v.isdigit(): return int(v)
    return v


def unit_loc(r):
    """-> (tuple of LOC_FIELDS values or None, last heading). Integers stay integers: small in SQLite."""
    loc = tuple(_compact(r.get(k)) for k in LOC_FIELDS)
    h = r.get("headings")
    head = (h[-1] if isinstance(h, list) and h else r.get("poem_title") or "") or ""
    return (loc if any(x is not None for x in loc) else None), " ".join(str(head).split())[:160]


def unit_text(r):
    if r.get("hemistichs"):
        return " / ".join(r["hemistichs"])
    return r.get("text") or ""


def iter_units(repo, only=()):
    idx = {}
    for r in csv.DictReader(open(os.path.join(repo, "catalogs/works_index.tsv"), encoding="utf-8"), delimiter="\t"):
        idx[r["corpus_path"]] = r
    oc = json.load(open(os.path.join(repo, "catalogs/openiti_catalog.json"), encoding="utf-8"))
    oc = oc.get("works", oc)
    ver2work = {v["file"]: (k, w) for k, w in oc.items() for v in w["versions"]}
    # Mathnawi
    for b in range(1, 7):
        p = os.path.join(repo, f"corpus/mathnawi/book{b}.tsv")
        for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
            if only and not any(o in "rumi.mathnawi" or o in p for o in only): break
            yield dict(uid=r["id"], work_key="rumi.mathnawi", author="rumi", lang="fa", attribution="secure",
                       source_type="ganjoor", primary_version=1,
                       text=f'{r["hemistich_1"]} / {r["hemistich_2"]}', loc=None, head="")  # the uid is the Nicholson number
    for p in sorted(glob.glob(os.path.join(repo, "corpus/**/*.jsonl"), recursive=True) +
                    glob.glob(os.path.join(repo, "corpus/**/*.jsonl.gz"), recursive=True)):
        rel = os.path.relpath(p, repo)
        if rel.startswith("corpus/mathnawi/"):
            continue
        if rel.startswith("corpus/openiti/"):
            full = os.path.basename(p)[:-6]; ver = full.replace(".completed", "")
            wk, w = ver2work.get(full) or ver2work.get(ver) or (ver.rsplit(".", 1)[0], {})
            meta = dict(work_key=ver, author=OPENITI_AUTHOR.get(ver.split(".")[0], ver.split(".")[0]), lang="ar",
                        attribution=w.get("attribution", "unreviewed"), source_type="openiti",
                        primary_version=int(not w or w.get("primary") in (full, ver)))
        else:
            r = idx.get(rel)
            if r is None:
                print("not in works_index, skipped:", rel); continue
            fa = r["source_type"] == "ganjoor" or r["author"] in PERSIAN_AUTHORS
            meta = dict(work_key=r["key"], author=r["author"], lang="fa" if fa else "ar",
                        attribution=r["attribution"], source_type=r["source_type"], primary_version=1)
        if only and not any(o in meta["work_key"] or o in rel for o in only):
            continue
        for line in (gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")):
            rec = json.loads(line)
            t = unit_text(rec)
            if t.strip():
                loc, head = unit_loc(rec)
                yield dict(uid=rec["id"], text=t, loc=loc, head=head, **meta)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--out", default="search/library.sqlite")
    ap.add_argument("--only", default="", help="sample build: comma-separated substrings of work keys / corpus paths")
    ap.add_argument("--add-citations", action="store_true", help="add the v32 citation layer to an existing index at --out")
    a = ap.parse_args()
    only = tuple(x for x in a.only.split(",") if x)
    if a.add_citations:
        db = sqlite3.connect(a.out)
        db.execute("DELETE FROM meta WHERE k LIKE 'citations%'")
        db.executescript("DROP TABLE IF EXISTS unit_loc; DROP TABLE IF EXISTS heads;" + LOC_DDL)
        rid = dict(db.execute("SELECT uid, rowid FROM units"))
        heads = {}
        db.executemany("INSERT OR IGNORE INTO unit_loc VALUES(?,?,?,?,?,?,?,?,?)",
                       ((rid[u["uid"]], *(u["loc"] or (None,) * 7), head_id(heads, u["head"])) for u in iter_units(a.repo, only)
                        if u["uid"] in rid and (u["loc"] or u["head"])))
        db.executemany("INSERT INTO heads VALUES(?,?)", ((i, h) for h, i in heads.items())); del rid
        ok = add_citation_tables(db, a.repo)
        make_works_table(db, ok, replace=True)
        self_check(db)
        db.commit(); db.execute("VACUUM"); db.close()
        return
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    an = Analyzer(MorphologyDB.builtin_db(), backoff="NONE")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    if os.path.exists(a.out): os.remove(a.out)
    db = sqlite3.connect(a.out)
    db.executescript("""
      PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
      CREATE TABLE units(rowid INTEGER PRIMARY KEY, uid TEXT, work_key TEXT, author TEXT, lang TEXT,
                         attribution TEXT, source_type TEXT, primary_version INT, text TEXT);
      CREATE VIRTUAL TABLE fts USING fts5(norm, roots, content='', tokenize="unicode61 remove_diacritics 0");
      CREATE TABLE vocab(word TEXT PRIMARY KEY, roots TEXT, freq INT);
      CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
    """ + LOC_DDL)
    cache = {}; freq = collections.Counter(); t0 = time.time(); n = 0; heads = {}
    def roots_of(w):
        r = cache.get(w)
        if r is None:
            q = w.replace("ی", "ي").replace("ک", "ك")
            r = " ".join(sorted({root_token(x["root"]) for x in an.analyze(q)
                                 if x.get("root") and x["root"] not in SKIP_ROOTS and "." in x["root"]}))
            cache[w] = r
        return r
    batch = []
    for u in iter_units(a.repo, only):
        ws = words(u["text"]); freq.update(ws)
        roots = " ".join(filter(None, (roots_of(w) for w in ws)))
        n += 1
        batch.append((n, u["uid"], u["work_key"], u["author"], u["lang"], u["attribution"], u["source_type"],
                      u["primary_version"], u["text"], norm(u["text"]), roots, u["loc"], head_id(heads, u["head"])))
        if len(batch) >= 20000:
            flush(db, batch); batch = []
            print(f"{n} units, {len(cache)} types, {time.time()-t0:.0f}s", flush=True)
    flush(db, batch)
    db.executemany("INSERT INTO vocab VALUES(?,?,?)", ((w, cache.get(w, ""), c) for w, c in freq.items()))
    db.executemany("INSERT INTO heads VALUES(?,?)", ((i, h) for h, i in heads.items()))
    add_hadith_tables(db, a.repo)
    db.executescript("CREATE INDEX units_work ON units(work_key); CREATE INDEX units_uid ON units(uid);")
    ok = add_citation_tables(db, a.repo)
    make_works_table(db, ok)
    db.execute("INSERT INTO fts(fts) VALUES('optimize')")
    try: commit = subprocess.check_output(["git", "-C", a.repo, "rev-parse", "HEAD"], text=True).strip()
    except Exception: commit = "unknown"
    import camel_tools
    db.executemany("INSERT INTO meta VALUES(?,?)", [("repo_commit", commit), ("camel_tools", camel_tools.__version__),
        ("camel_db", "morphology-db-msa-r13"), ("units", str(n)), ("types", str(len(freq))),
        ("built", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))] + ([("sample", a.only)] if only else []))
    self_check(db)
    db.commit(); db.execute("VACUUM"); db.close()
    print(f"done: {n} units, {len(freq)} word types, {time.time()-t0:.0f}s -> {a.out}")


def narrator_key(s):
    """Normalised narrator name for lookups (same rule in search.py): norm + Abi/Aba -> Abu, Ibn -> bin."""
    import re
    s = re.sub(r"[^ء-ي ]", " ", norm(s or ""))
    s = re.sub(r"\bابي\b", "ابو", s); s = re.sub(r"\bابا\b", "ابو", s); s = re.sub(r"\bابن\b", "بن", s)
    return " ".join(s.split())


def add_hadith_tables(db, repo):
    """v17: hadith layer (apparatus/hadith, v16) + links (apparatus/hadith_links, v17) as tables:
    hadith(hadith_id, collection, number, narrator, narrator_key, caliph, grades, parallel_group,
           parallel_collections, agreed_upon, weakest_rank, weakest_rank_name, linked, names)
    hadith_units(uid, hadith_id)  - corpus units a hadith was assembled from (join to units.uid)"""
    files = sorted(glob.glob(os.path.join(repo, "apparatus/hadith/*.jsonl.gz")))
    if not files: return
    db.executescript("""
      CREATE TABLE hadith(hadith_id TEXT PRIMARY KEY, collection TEXT, number TEXT, narrator TEXT, narrator_key TEXT,
                          caliph TEXT, grades TEXT, parallel_group TEXT, parallel_collections INT, agreed_upon INT,
                          weakest_rank INT, weakest_rank_name TEXT, linked INT, names INT);
      CREATE TABLE hadith_units(uid TEXT, hadith_id TEXT);""")
    links = {}
    lp = os.path.join(repo, "apparatus/hadith_links/chains.jsonl.gz")
    if os.path.exists(lp):
        for line in gzip.open(lp, "rt", encoding="utf-8"):
            r = json.loads(line)
            links[r["hadith_id"]] = (r["parallel_group"], r["parallel_collections"], int(r["agreed_upon"]),
                                     r["weakest_rank"], r["weakest_rank_name"], r["linked"], r["names"])
    n = 0
    for p in files:
        rows, units = [], []
        for line in gzip.open(p, "rt", encoding="utf-8"):
            h = json.loads(line)
            g = "; ".join(f'{x["by"]}: {x["grade"]}' for x in h["grades"])
            L = links.get(h["id"], (None, 1, 0, None, None, None, None))
            rows.append((h["id"], h["collection"], str(h["number"]), h["narrator"], narrator_key(h["narrator"]),
                         h["caliph"], g, *L))
            units += [(u, h["id"]) for u in h["source_ids"]]
        db.executemany("INSERT OR IGNORE INTO hadith VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        db.executemany("INSERT INTO hadith_units VALUES(?,?)", units); n += len(rows)
    db.executescript("""CREATE INDEX hu_uid ON hadith_units(uid); CREATE INDEX h_nar ON hadith(narrator_key);
                        CREATE INDEX h_cal ON hadith(caliph); CREATE INDEX h_grp ON hadith(parallel_group);""")
    db.execute("INSERT OR REPLACE INTO meta VALUES('hadith', ?)", (str(n),))
    print(f"hadith tables: {n} hadith", flush=True)


def flush(db, batch):
    db.executemany("INSERT INTO units VALUES(?,?,?,?,?,?,?,?,?)", [b[:9] for b in batch])
    db.executemany("INSERT INTO fts(rowid, norm, roots) VALUES(?,?,?)", [(b[0], b[9], b[10]) for b in batch])
    db.executemany("INSERT INTO unit_loc VALUES(?,?,?,?,?,?,?,?,?)",
                   [(b[0], *(b[11] or (None,) * 7), b[12]) for b in batch if b[11] or b[12]])


CITATION_TABLES = ("work_meta", "unit_conf", "verse_refs", "concept_refs", "concepts")


def _tsv(repo, rel):
    p = os.path.join(repo, rel)
    if not os.path.exists(p): return None
    f = gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")
    return csv.DictReader(f, delimiter="\t")


def _int(x):
    try: return int(x)
    except (TypeError, ValueError): return None


def _float(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def _run(db, script):
    # not executescript(): that commits first, which would end the savepoint
    for st in script.split(";"):
        if st.strip(): db.execute(st)


def add_citation_tables(db, repo):
    """v32: merge the citation data (reports/index, reports/collation) into the index, joined to units by uid.
    Runs inside a savepoint: on any error the partial tables are rolled back, a warning is printed, and the
    build continues, so a bad citation file can cost the citation layer but never the index."""
    import re
    db.execute("SAVEPOINT cit")
    try:
        for t in CITATION_TABLES: db.execute(f"DROP TABLE IF EXISTS {t}")
        for t in ("t_conf", "t_verse", "t_concept"): db.execute(f"DROP TABLE IF EXISTS temp.{t}")
        _run(db, """
          CREATE TABLE work_meta(work_key TEXT PRIMARY KEY, title TEXT, death_ah INT, source_type TEXT, witnesses INT,
                                 corroborated INT, checked INT, refs TEXT, page_note TEXT);
          CREATE TABLE unit_conf(unit INTEGER PRIMARY KEY, level TEXT, ocr_score REAL, agreement REAL, witness TEXT);
          CREATE TABLE verse_refs(unit INT, sura INT, aya INT, how TEXT, hits INT);
          CREATE TABLE concept_refs(unit INT, concept TEXT, n INT);
          CREATE TEMP TABLE t_conf(uid TEXT, level TEXT, ocr_score REAL, agreement REAL, witness TEXT);
          CREATE TEMP TABLE t_verse(uid TEXT, sura INT, aya INT, how TEXT, hits INT);
          CREATE TEMP TABLE t_concept(uid TEXT, concept TEXT, n INT);
          CREATE TABLE concepts(concept TEXT PRIMARY KEY, label TEXT, area TEXT, works INT, passages INT);""")
        rows = []
        for r in _tsv(repo, "reports/index/works_meta.tsv") or []:
            c, _, k = (r.get("corroborated_of_checked") or "").partition("/")
            rows.append((r["key"], r["title"], _int(r["death_ah"]), r["source_type"], _int(r["witnesses"]),
                         _int(c), _int(k), r["references"] or None, r["page_note"] or None))
        db.executemany("INSERT OR REPLACE INTO work_meta VALUES(?,?,?,?,?,?,?,?,?)", rows)
        # works not in works_meta.tsv (the OpenITI versions): death year from the name, e.g. 0505Ghazali -> 505
        extra = []
        for wk, st in db.execute("SELECT DISTINCT work_key, source_type FROM units WHERE work_key NOT IN (SELECT work_key FROM work_meta)"):
            m = re.search(r"(?:^|\.)(\d{4})[A-Z]", wk)
            extra.append((wk, wk, int(m.group(1)) if m else None, st, None, None, None, None, None))
        db.executemany("INSERT INTO work_meta VALUES(?,?,?,?,?,?,?,?,?)", extra)
        db.execute("UPDATE work_meta SET death_ah = 0 WHERE work_key LIKE '%0001Quran%'")  # the Qur'an sorts first, shows no death year
        db.executemany("INSERT INTO t_conf VALUES(?,?,?,?,?)",
                       ((r["record_id"], r["level"], _float(r["ocr_score"]), _float(r["best_agreement"]), r["best_witness"] or None)
                        for r in _tsv(repo, "reports/collation/confidence.tsv.gz") or []))
        db.executemany("INSERT INTO t_verse VALUES(?,?,?,?,?)",
                       ((r["record_id"], int(r["sura"]), int(r["aya"]), r["how"], _int(r["hits"]))
                        for r in _tsv(repo, "reports/index/verse_index.tsv.gz") or []))
        # the verse itself, so --verse also returns the Qur'an text (how = verse)
        db.execute("""INSERT INTO t_verse SELECT uid, CAST(substr(uid, 11, instr(substr(uid, 11), ':') - 1) AS INT),
                      CAST(substr(substr(uid, 11), instr(substr(uid, 11), ':') + 1) AS INT), 'verse', 1
                      FROM units WHERE uid GLOB 'urn:quran:[0-9]*:[0-9]*'""")
        db.executemany("INSERT INTO t_concept VALUES(?,?,?)",
                       ((r["record_id"], r["concept"], _int(r["n"])) for r in _tsv(repo, "reports/index/concept_index.tsv.gz") or []))
        db.executemany("INSERT OR REPLACE INTO concepts VALUES(?,?,?,?,?)",
                       ((r["concept"], r["label"], r["area"], _int(r["works"]), _int(r["passages"]))
                        for r in _tsv(repo, "reports/index/concept_summary.tsv") or []))
        raw = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("t_verse", "t_conf", "t_concept")}
        # keep only rows that resolve to an indexed unit (sample builds resolve few; that's expected)
        _run(db, """INSERT OR REPLACE INTO unit_conf SELECT u.rowid, t.level, t.ocr_score, t.agreement, t.witness
                      FROM t_conf t JOIN units u ON u.uid = t.uid;
                    INSERT INTO verse_refs SELECT u.rowid, t.sura, t.aya, t.how, t.hits FROM t_verse t JOIN units u ON u.uid = t.uid
                      ORDER BY t.sura, t.aya, u.rowid;
                    INSERT INTO concept_refs SELECT u.rowid, t.concept, t.n FROM t_concept t JOIN units u ON u.uid = t.uid;
                    DROP TABLE t_conf; DROP TABLE t_verse; DROP TABLE t_concept""")
        _run(db, """CREATE INDEX vr_verse ON verse_refs(sura, aya, unit); CREATE INDEX vr_unit ON verse_refs(unit);
                            CREATE INDEX cr_concept ON concept_refs(concept, unit); CREATE INDEX cr_unit ON concept_refs(unit);""")
        n = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in CITATION_TABLES}
        db.executemany("INSERT OR REPLACE INTO meta VALUES(?,?)", [("citations", "ok"), ("citations_counts", json.dumps(n)),
            ("citations_source_rows", json.dumps({"verse_refs": raw["t_verse"], "unit_conf": raw["t_conf"], "concept_refs": raw["t_concept"]}))])
        db.execute("RELEASE cit")
        print(f"citation tables: {n} (resolved from source rows {raw})", flush=True)
        return True
    except Exception as e:
        db.execute("ROLLBACK TO cit"); db.execute("RELEASE cit")
        db.execute("INSERT OR REPLACE INTO meta VALUES('citations', ?)", (f"failed: {type(e).__name__}: {e}"[:500],))
        print(f"::warning::citation layer skipped ({type(e).__name__}: {e}); the index is built without it", flush=True)
        return False


def make_works_table(db, with_meta, replace=False):
    if replace: db.execute("DROP TABLE IF EXISTS works")
    if with_meta:
        db.execute("""CREATE TABLE works AS SELECT u.work_key, u.author, u.lang, u.attribution, u.source_type, u.primary_version,
                        COUNT(*) AS units, m.title, m.death_ah, m.witnesses, m.corroborated, m.checked, m.refs, m.page_note
                      FROM units u LEFT JOIN work_meta m ON m.work_key = u.work_key GROUP BY u.work_key""")
    else:
        db.execute("""CREATE TABLE works AS SELECT work_key, author, lang, attribution, source_type, primary_version,
                        COUNT(*) AS units FROM units GROUP BY work_key""")


def self_check(db):
    """Print a few sanity facts (never fails the build)."""
    try:
        q = lambda s: db.execute(s).fetchone()[0]
        print("self-check: units", q("SELECT COUNT(*) FROM units"), "| works", q("SELECT COUNT(*) FROM works"),
              "| located", q("SELECT COUNT(*) FROM unit_loc"), "| citations", q("SELECT v FROM meta WHERE k='citations'"))
        if q("SELECT v FROM meta WHERE k='citations'") == "ok":
            print("self-check: 2:31 ->", q("SELECT COUNT(DISTINCT unit) FROM verse_refs WHERE sura=2 AND aya=31"),
                  "units; works without death year:", q("SELECT COUNT(*) FROM works WHERE death_ah IS NULL"))
    except Exception as e:
        print(f"::warning::self-check error: {e}")


if __name__ == "__main__":
    main()
