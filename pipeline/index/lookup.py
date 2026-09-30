#!/usr/bin/env python3
"""
lookup.py - v29: one command for one question. Given a verse, return every commentary passage on it and every
Sufi text that quotes it, each already citable (work, author's death year, locator) and graded (source type,
collation level where the text is OCR).

  python3 pipeline/index/lookup.py --repo . --verse 2:31            # all works
  python3 pipeline/index/lookup.py --repo . --verse 24:35 --how lemma,heading --chars 400
  python3 pipeline/index/lookup.py --repo . --concept qutb --work wilaya,ibnarabi.futuhat.arabiyya   (v30)
  python3 pipeline/index/lookup.py --repo . --build-meta            # (re)write reports/index/works_meta.tsv

Reads reports/index/verse_index.tsv.gz (build_verse_index.py), catalogs/works_index.tsv,
reports/collation/confidence.tsv.gz, catalogs/witnesses.tsv and catalogs/secondary_literature.tsv.
works_meta.tsv, one row per work: key, title, death_ah (from the OpenITI-style name, e.g. 0310 = d. 310 AH, or the
author's folder: ibnarabi 638, jilani 561, shams 645, aflaki 761, mathnawi 672, ghazali 505),
source_type, witnesses, pages corroborated / checked, secondary references, and a page note where one is known.
"""
import argparse, collections, csv, gzip, json, os, re

FOLDER_DEATH = {"ibnarabi": 638, "jilani": 561, "shams": 645, "aflaki": 761, "mathnawi": 672, "ghazali": 505}
DEATH_OVERRIDE = {"jami": 898, "qashani": 736, "qaysari": 751, "parsa": 822, "rahma": "", "bursevi": 1137}  # works by others in author folders
PAGE_NOTES = {"shams.maqalat.movahhed_ocr": "printed_page runs one ahead of the page header: cite printed_page - 1 (v25)"}


def rd(repo, p):
    p = os.path.join(repo, p)
    if not os.path.exists(p): return []
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f: return list(csv.DictReader(f, delimiter="\t"))


def build_meta(repo):
    idx = rd(repo, "catalogs/works_index.tsv")
    wit = collections.Counter(r["work_key"] for r in rd(repo, "catalogs/witnesses.tsv"))
    conf = {r["work"]: r for r in rd(repo, "reports/collation/confidence_summary.tsv")}
    refs = collections.defaultdict(list)
    for r in rd(repo, "catalogs/secondary_literature.tsv"):
        for k in (r.get("covers") or "").split(";"):
            if k.strip(): refs[k.strip()].append(r["ref_id"])
    rows = []
    for w in idx:
        m = re.search(r"(?:^|\.)(\d{4})[A-Z]", w["key"])
        c = conf.get(w["key"], {})
        ref = refs.get(w["key"], []) + [r for k, v in refs.items() if k.endswith(".*") and w["key"].startswith(k[:-1]) for r in v]
        ov = next((v for k, v in DEATH_OVERRIDE.items() if k in w["key"].lower()), None)
        rows.append([w["key"], w["work"], int(m.group(1)) if m else ov if ov is not None else FOLDER_DEATH.get(w["key"].split(".")[0], ""), w["source_type"], wit.get(w["key"], 0),
                     f"{c.get('corroborated', '')}/{c.get('records', '')}" if c else "", ";".join(ref), PAGE_NOTES.get(w["key"], "")])
    os.makedirs(os.path.join(repo, "reports/index"), exist_ok=True)
    with open(os.path.join(repo, "reports/index/works_meta.tsv"), "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n")
        c.writerow(["key", "title", "death_ah", "source_type", "witnesses", "corroborated_of_checked", "references", "page_note"])
        c.writerows(rows)
    print(len(rows), "works in reports/index/works_meta.tsv")


def lookup(repo, verse, hows, chars, per_work, concept=None, works=()):
    hits = collections.defaultdict(list)
    keep = lambda k: not works or any(k == w or k.startswith(w + ".") or k.split(".")[0] == w for w in works)
    if concept:
        with gzip.open(os.path.join(repo, "reports/index/concept_index.tsv.gz"), "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["concept"] == concept and keep(r["work"]): r["how"] = f"x{r['n']}"; hits[r["work"]].append(r)
        for k in hits: hits[k].sort(key=lambda r: -int(r["n"]))
        verse = f"concept {concept}"
    else:
        s, a = verse.split(":")
        with gzip.open(os.path.join(repo, "reports/index/verse_index.tsv.gz"), "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["sura"] == s and r["aya"] == a and (not hows or r["how"] in hows) and keep(r["work"]): hits[r["work"]].append(r)
    meta = {r["key"]: r for r in rd(repo, "reports/index/works_meta.tsv")}
    idx = {r["key"]: r for r in rd(repo, "catalogs/works_index.tsv")}
    want = {r["record_id"] for rs in hits.values() for r in rs}
    level = {}
    p = os.path.join(repo, "reports/collation/confidence.tsv.gz")
    if os.path.exists(p):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["record_id"] in want: level[r["record_id"]] = r["level"]
    order = sorted(hits, key=lambda k: (int(meta.get(k, {}).get("death_ah") or 9999), k))
    print(f"{verse}: {sum(len(v) for v in hits.values())} passages in {len(hits)} works\n")
    for k in order:
        m = meta.get(k, {}); rs = hits[k]; shown = {r["record_id"] for r in rs[:per_work]}
        print(f"## {m.get('title', k)}  (d. {m.get('death_ah') or '?'} AH; {m.get('source_type', '?')}"
              f"{'; ' + m['page_note'] if m.get('page_note') else ''})  {dict(collections.Counter(r['how'] for r in rs))}")
        cp = os.path.join(repo, idx[k]["corpus_path"]) if k in idx else None
        if cp and os.path.exists(cp):
            op = gzip.open if cp.endswith(".gz") else open
            with op(cp, "rt", encoding="utf-8") as f:
                for l in f:
                    if not shown: break
                    r = json.loads(l)
                    if r.get("id") in shown:
                        shown.discard(r["id"])
                        loc = " ".join(f"{x}={r[x]}" for x in ("vol", "page_before", "page", "leaf", "printed_page") if r.get(x))
                        how = next(x["how"] for x in rs if x["record_id"] == r["id"])
                        t = re.sub(r"\s+", " ", r.get("text") or r.get("text_raw") or "")[:chars]
                        print(f"- [{how}] {r['id'].split(':')[-1]} {loc} {('[' + level[r['id']] + ']') if r['id'] in level else ''}\n  {t}")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    ap.add_argument("--verse"); ap.add_argument("--how", default=""); ap.add_argument("--chars", type=int, default=300)
    ap.add_argument("--per-work", type=int, default=3); ap.add_argument("--build-meta", action="store_true")
    ap.add_argument("--concept"); ap.add_argument("--work", default="", help="limit to collections or work keys, comma-separated")
    a = ap.parse_args()
    if a.build_meta: build_meta(a.repo)
    ws = [w for w in a.work.split(",") if w]
    if a.verse or a.concept:
        lookup(a.repo, a.verse, set(filter(None, a.how.split(","))), a.chars, a.per_work, a.concept, ws)
