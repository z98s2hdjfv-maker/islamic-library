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

Roots: every distinct word type is analysed once with CAMeL Tools (morphology-db-msa-r13,
no backoff); the union of roots over all analyses is stored, so root search favours recall.
Persian texts are analysed too (after ی->ي, ک->ك) - this catches Arabic loanwords such as
توکل, but Persian words can pick up spurious Arabic roots; filter with --lang when it matters.

Skips corpus/mathnawi/full/ (same couplets as corpus/mathnawi/book*.tsv, which carry the
Nicholson IDs). OpenITI: all versions are indexed; primary_version=1 marks the catalog's
primary one (search.py uses only primary versions unless --all-versions).

Usage: python3 pipeline/search/build_index.py --repo . --out search/library.sqlite
Needs: pip install camel-tools ; camel_data -i morphology-db-msa-r13
"""
import argparse, csv, glob, gzip, json, os, sqlite3, subprocess, sys, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textnorm import norm, words, root_token

SKIP_ROOTS = {"PUNC", "DIGIT", "FOREIGN", "NTWS", "LATIN", "NOAN"}
OPENITI_AUTHOR = {"0505Ghazali": "ghazali", "0561CabdQadirJilani": "jilani", "0638IbnCarabi": "ibnarabi"}
PERSIAN_AUTHORS = {"shams", "aflaki"}


def unit_text(r):
    if r.get("hemistichs"):
        return " / ".join(r["hemistichs"])
    return r.get("text") or ""


def iter_units(repo):
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
            yield dict(uid=r["id"], work_key="rumi.mathnawi", author="rumi", lang="fa", attribution="secure",
                       source_type="ganjoor", primary_version=1,
                       text=f'{r["hemistich_1"]} / {r["hemistich_2"]}')
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
        for line in (gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")):
            rec = json.loads(line)
            t = unit_text(rec)
            if t.strip():
                yield dict(uid=rec["id"], text=t, **meta)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--out", default="search/library.sqlite")
    a = ap.parse_args()
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
    """)
    cache = {}; freq = collections.Counter(); t0 = time.time(); n = 0
    def roots_of(w):
        r = cache.get(w)
        if r is None:
            q = w.replace("ی", "ي").replace("ک", "ك")
            r = " ".join(sorted({root_token(x["root"]) for x in an.analyze(q)
                                 if x.get("root") and x["root"] not in SKIP_ROOTS and "." in x["root"]}))
            cache[w] = r
        return r
    batch = []
    for u in iter_units(a.repo):
        ws = words(u["text"]); freq.update(ws)
        roots = " ".join(filter(None, (roots_of(w) for w in ws)))
        n += 1
        batch.append((n, u["uid"], u["work_key"], u["author"], u["lang"], u["attribution"], u["source_type"],
                      u["primary_version"], u["text"], norm(u["text"]), roots))
        if len(batch) >= 20000:
            flush(db, batch); batch = []
            print(f"{n} units, {len(cache)} types, {time.time()-t0:.0f}s", flush=True)
    flush(db, batch)
    db.executemany("INSERT INTO vocab VALUES(?,?,?)", ((w, cache.get(w, ""), c) for w, c in freq.items()))
    add_hadith_tables(db, a.repo)
    db.executescript("""
      CREATE INDEX units_work ON units(work_key); CREATE INDEX units_uid ON units(uid);
      CREATE TABLE works AS SELECT work_key, author, lang, attribution, source_type, primary_version,
             COUNT(*) AS units FROM units GROUP BY work_key;
      INSERT INTO fts(fts) VALUES('optimize');
    """)
    try: commit = subprocess.check_output(["git", "-C", a.repo, "rev-parse", "HEAD"], text=True).strip()
    except Exception: commit = "unknown"
    import camel_tools
    db.executemany("INSERT INTO meta VALUES(?,?)", [("repo_commit", commit), ("camel_tools", camel_tools.__version__),
        ("camel_db", "morphology-db-msa-r13"), ("units", str(n)), ("types", str(len(freq))),
        ("built", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))])
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


if __name__ == "__main__":
    main()
