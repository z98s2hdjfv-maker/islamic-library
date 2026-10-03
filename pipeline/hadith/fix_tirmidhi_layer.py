#!/usr/bin/env python3
"""
fix_tirmidhi_layer.py - v53: the hadith of al-Tirmidhi's Sunan that the v16 layer missed.

The v16 build started a hadith only where a paragraph began with a transmission verb (haddathana ...). In the JK
text of al-Tirmidhi about 250 paragraphs begin otherwise: with the basmala at the head of a book ("bismillah ...
haddathana Qutayba ..."), with the editor's mark "m", with "qala wa-haddathana", or with a report given without its
chain first ("wa-qad ruwiya ..."). Such a paragraph was either dropped (when it came first under a heading) or glued
to the end of the hadith before it. Among them: the black spot on the heart (Shakir 3334) and "He was in a cloud"
(3109), both asked for in the live cases and not found.

What this does
  - walks corpus/hadith/0279Tirmidhi.Sunan.jsonl.gz again with the wider rule;
  - every hadith already in the layer keeps its id and number (matched by its first source paragraph). Where a
    stray paragraph had been glued to it, its text is rebuilt without that paragraph;
  - every hadith found now gets the id urn:hadith:0279Tirmidhi.Sunan:p<paragraph number> (number "pNNNNN"), in
    its place in the book, marked "added": "v53";
  - the Shakir / Abd al-Baqi numbers are read again from the headings for all of them
    (apparatus/hadith_numbers/0279Tirmidhi.Sunan.tsv is rewritten).
Nothing is fetched. Run once; running it again changes nothing.
Usage: python3 pipeline/hadith/fix_tirmidhi_layer.py --repo .
"""
import argparse, collections, csv, gzip, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hadith_layer as B

COL = "0279Tirmidhi.Sunan"
EDITION = "Shakir / ʿAbd al-Baqi numbering"
BASMALA = re.compile(r"^\s*بسم الله الرحمن الرحيم\s*")
PREFIX = re.compile(r"^\s*(?:م|قال)\s+(?=و?(?:حدثنا|حدثني|أخبرنا|أخبرني))")


def clean(t):
    t = re.sub(r"^\s*#+\s*\$+\s*", "", t or "")
    return re.sub(r"^\s*\d+\s*[-–]?\s+(?=\S)", "", t)


def starts(t):
    """(is a new hadith, text to keep). The wider rule of v53."""
    if B.START_VERB.match(t): return True, t
    u = BASMALA.sub("", t)
    u2 = PREFIX.sub("", u)
    if B.START_VERB.match(u2): return True, u2
    if "*" in u and not u.lstrip().startswith(("~~", "#", "(")) and len(u.split()) >= 8: return True, u
    return False, t


def units(path):
    cur = None; ed = None
    for line in gzip.open(path, "rt", encoding="utf-8"):
        r = json.loads(line)
        if r["kind"] == "heading":
            m = re.fullmatch(r"#+\s*\|+\s*(\d+)\s*", r.get("text_raw", ""))
            if m: ed = int(m.group(1))
            if cur: yield cur
            cur = None; continue
        t = clean(r.get("text"))
        new, t = starts(t)
        if new:
            if cur: yield cur
            cur = {"ids": [r["id"]], "text": t, "heads": r.get("headings") or [], "ed": ed}; ed = None
        elif cur:
            cur["ids"].append(r["id"]); cur["text"] += " " + t
    if cur: yield cur


def record(u, old):
    text = B.TAILNUM.sub("", u["text"]).strip()
    isnad, matn, how = B.split(text)
    c = B.narrator(isnad) if isnad else None
    grades = [{"by": "al-Tirmidhi", "grade": g.group(1).strip(), "text": g.group(0), "method": "inline"}
              for g in B.GRADE.finditer(matn)]
    if old:
        rec = dict(old)
        if old["source_ids"] == u["ids"]: return rec, False          # untouched
    else:
        n = "p" + u["ids"][0].rsplit(":p", 1)[1]
        rec = {"id": f"urn:hadith:{COL}:{n}", "collection": COL, "number": n, "numbering": "paragraph (added v53)"}
    rec.update({"chapter": u["heads"][-1] if u["heads"] else None, "isnad": isnad, "matn": matn, "split_method": how,
                "narrator": c, "caliph": B.CALIPHS.get(c) if c else None, "grades": grades,
                "comments": [m.group(1).strip() for m in B.COMMENT.finditer(matn)][:5],
                "source_ids": u["ids"], "status": "unverified"})
    if not old: rec["added"] = "v53"
    else: rec["rebuilt"] = "v53"
    return rec, True


def main(repo):
    lp = os.path.join(repo, f"apparatus/hadith/{COL}.jsonl.gz")
    layer = [json.loads(l) for l in gzip.open(lp, "rt", encoding="utf-8")]
    by_first = {h["source_ids"][0]: h for h in layer}
    out, seen, stats = [], set(), collections.Counter()
    for u in units(os.path.join(repo, f"corpus/hadith/{COL}.jsonl.gz")):
        old = by_first.get(u["ids"][0])
        rec, changed = record(u, old)
        rec.pop("edition_numbers", None); rec["_ed"] = u["ed"]
        out.append(rec); seen.add(rec["id"])
        stats["kept" if old and not changed else "rebuilt" if old else "added"] += 1
    lost = [h["id"] for h in layer if h["id"] not in seen]
    if lost: sys.exit(f"would lose {len(lost)} hadith ids, e.g. {lost[:5]}: nothing written")
    cnt = collections.Counter(r["_ed"] for r in out if r["_ed"] is not None)
    with open(os.path.join(repo, f"apparatus/hadith_numbers/{COL}.tsv"), "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n")
        c.writerow(["hadith_id", "layer_number", "edition_number", "edition", "method", "match", "uncertain"])
        for r in out:
            n = r.pop("_ed")
            if n is None: continue
            unc = "shared number" if cnt[n] > 1 else ""
            r["edition_numbers"] = [{"number": n, "edition": EDITION, **({"uncertain": unc} if unc else {})}]
            c.writerow([r["id"], r["number"], n, EDITION, "heading in the layer's own text", "", unc]); stats["numbered"] += 1
    with open(lp, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
         io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
        for r in out: fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    sp = os.path.join(repo, "catalogs/hadith_layer_summary.json")
    s = json.load(open(sp, encoding="utf-8"))
    before = s["collections"][COL].get("hadith", len(layer))
    s["collections"][COL]["hadith"] = len(out)
    s["collections"][COL]["v53"] = f"{stats['added']} hadith added and {stats['rebuilt']} rebuilt by fix_tirmidhi_layer.py"
    if "totals" in s and "hadith" in s["totals"]: s["totals"]["hadith"] += len(out) - before
    json.dump(s, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if stats["added"]:      # the coverage figures of catalogs/critic_grades_summary.json, kept in step (the new hadith have
        added = [r for r in out if r.get("added") == "v53"]   # the compiler's own grade or nothing; no critic or modern rows yet)
        graded = sum(1 for r in added if r["grades"]); bare = len(added) - graded
        cp = os.path.join(repo, "catalogs/critic_grades_summary.json"); g = json.load(open(cp, encoding="utf-8"))
        for cov in (g["coverage"], g["coverage"]["by_collection"][COL]):
            cov["hadith"] += len(added); cov["compiler_grade"] += graded
            for k in ("no_classical_grade", "nothing_at_all", "no_grade_classical_or_modern"): cov[k] += bare
        g["coverage"]["v53"] = f"{len(added)} hadith of al-Tirmidhi added to the layer ({graded} with his own grade); the critics' and modern tables were not rebuilt for them"
        json.dump(g, open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{COL}: {len(layer)} -> {len(out)} hadith", dict(stats), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    main(os.path.abspath(ap.parse_args().repo))
