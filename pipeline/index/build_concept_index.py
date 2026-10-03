#!/usr/bin/env python3
"""
build_concept_index.py - v30: where each key term of our study occurs, across the collections.

catalogs/concepts.tsv   concept id, English label, area (wilaya / nur / asma / address / path / creed), its Arabic
                        forms separated by "|", a note on known ambiguities, and (v38) cues and exclude.
                        Add a row to add a concept. The Futuhat is held in four versions, so it counts up to four times.
A form matches as a whole word or phrase, optionally after the prefixes و ف ب ل ك. Forms, cues and exclude words
are normalised here with the search normaliser (pipeline/search/textnorm.py), so they can be written plainly.

v38 sense filter. Many terms have everyday senses (al-qadaʾ is also a judgeship and making up a missed fast;
al-afrad also grammatical singulars; al-muʿallaq also a hadith with a suspended chain). A match of a SINGLE-WORD
form counts only if a cue word occurs within WINDOW characters around it (about 25 words) and no exclude word does;
multi-word phrases always count. Concepts with no cues or exclude are unfiltered.

Output (reports/index/):
  concept_index.tsv.gz    concept, work, record_id, n (kept occurrences in that passage)
  concept_summary.tsv     concept, label, area, works, passages, raw_passages (before the filter), kept_share,
                          filtered, the five works that use it most
lookup.py --concept qutb then lists the passages, oldest author first, cited and graded.
v53 Rumi. His works are in Persian (corpus/rumi, corpus/mathnawi) and were never indexed. catalogs/term_bridge.tsv
gives, for a concept, the Persian words he uses for it (malakut: عالم امر، لامکان، جهان جان ...). In the Persian
folders a concept matches by those words as well as by its Arabic forms; a Persian word always counts (no cue filter).
The Mathnawi's records hold their text as hemistichs; they are read too.

Usage: python3 pipeline/index/build_concept_index.py --repo . [--groups ...]
       python3 pipeline/index/build_concept_index.py --repo . --audit qada_qadar [--raw] [--n 20] [--groups tafsir,kalam]
         prints a random sample of kept (or, with --raw, unfiltered) hits in context, for judging precision.
"""
import argparse, collections, csv, glob, gzip, json, os, random, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from textnorm import norm  # noqa: E402

GROUPS = "ibnarabi,nur,wilaya,asma,jilani,sufi_manuals,tafsir_sufi,tafsir,shams,aflaki,ghazali,openiti,critics,hadith,afterlife,grading,modern,kalam,lugha,fitra,rumi,mathnawi"
PERSIAN = {"rumi", "mathnawi"}
WINDOW = 150


def word_rx(forms):
    forms = sorted({norm(f).strip() for f in forms if f.strip()}, key=len, reverse=True)
    return re.compile(r"(?:^|(?<=\s))[وفبلك]?(?:" + "|".join(re.escape(f) for f in forms) + r")(?=\s|$)") if forms else None


def compile_concepts(cons):
    return {c["concept"]: (word_rx(c["arabic_forms"].split("|")), word_rx((c.get("cues") or "").split("|")),
                           word_rx((c.get("exclude") or "").split("|"))) for c in cons}


def bridge(repo):
    """v53: concept -> regex of Rumi's Persian words for it (catalogs/term_bridge.tsv); no proclitics in Persian."""
    p = os.path.join(repo, "catalogs/term_bridge.tsv"); forms = collections.defaultdict(set)
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
            if r["concept"]: forms[r["concept"]] |= {norm(f).strip() for f in r["persian"].split("|") if f.strip()}
    return {c: re.compile(r"(?:^|(?<=\s))(?:" + "|".join(re.escape(f) for f in sorted(fs, key=len, reverse=True)) + r")(?=\s|$)")
            for c, fs in forms.items()}


def kept(t, m, cue, exc):
    if " " in m.group(0).strip(): return True                 # a multi-word phrase: unambiguous
    ctx = t[max(0, m.start() - WINDOW): m.start()] + " " + t[m.end(): m.end() + WINDOW]   # around the match, not the match
    if exc and exc.search(ctx): return False
    return not cue or bool(cue.search(ctx))


def iter_texts(repo, groups):
    for g in groups:
        for p in sorted(glob.glob(os.path.join(repo, "corpus", g, "*.jsonl*")) + glob.glob(os.path.join(repo, "corpus", g, "*", "*.jsonl*"))):
            work = f"{g}.{os.path.basename(p).split('.jsonl')[0]}"
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt", encoding="utf-8") as f:
                for l in f:
                    r = json.loads(l); t = r.get("text") or r.get("text_raw")
                    if r.get("hemistichs"): t = " ".join(r["hemistichs"])                     # Persian verse (v53)
                    elif isinstance(t, dict): t = " ".join((t.get("source") or {}).get("hemistichs") or [])   # the full Mathnawi
                    if not isinstance(t, str) or not t: continue
                    yield g, work, r.get("id", ""), " ".join(re.findall(r"[\u0621-\u064A\u067E\u0686\u0698\u06AF]+", norm(t)))


def load(repo):
    return list(csv.DictReader(open(os.path.join(repo, "catalogs/concepts.tsv"), encoding="utf-8"), delimiter="\t"))


def audit(repo, groups, cid, n, raw, seed=1):
    cons = {c["concept"]: c for c in load(repo)}
    rx, cue, exc = compile_concepts([cons[cid]])[cid]
    hits = [(rid, t[max(0, m.start() - 70): m.end() + 70]) for g, work, rid, t in iter_texts(repo, groups)
            for m in rx.finditer(t) if raw or kept(t, m, cue, exc)]
    random.seed(seed)
    for rid, ctx in random.sample(hits, min(n, len(hits))): print(f"{rid}\t{ctx}")
    print(f"# {cid}: {len(hits)} {'raw' if raw else 'kept'} hits", file=sys.stderr)


def main(repo, groups):
    cons = load(repo); pats = compile_concepts(cons); fa = bridge(repo)
    rows, per, rawp = [], collections.defaultdict(collections.Counter), collections.Counter()
    last = None
    for g, work, rid, t in iter_texts(repo, groups):
        if g != last and last: print(last, len(rows), flush=True)
        last = g
        for cid, (rx, cue, exc) in pats.items():
            ms = list(rx.finditer(t))
            pn = len(fa[cid].findall(t)) if g in PERSIAN and cid in fa else 0
            if not ms and not pn: continue
            rawp[cid] += 1
            n = sum(1 for m in ms if kept(t, m, cue, exc)) + pn
            if n: rows.append((cid, work, rid, n)); per[cid][work] += n
    print(last, len(rows), flush=True)
    out = os.path.join(repo, "reports/index"); os.makedirs(out, exist_ok=True)
    with gzip.open(os.path.join(out, "concept_index.tsv.gz"), "wt", encoding="utf-8", compresslevel=9) as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(["concept", "work", "record_id", "n"])
        w.writerows(sorted(rows))
    npass = collections.Counter(r[0] for r in rows)
    with open(os.path.join(out, "concept_summary.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["concept", "label", "area", "works", "passages", "raw_passages", "kept_share", "filtered", "top_works"])
        for c in cons:
            cid = c["concept"]
            w.writerow([cid, c["label"], c["area"], len(per[cid]), npass[cid], rawp[cid],
                        round(npass[cid] / rawp[cid], 3) if rawp[cid] else "", "yes" if (c.get("cues") or c.get("exclude")) else "no",
                        "; ".join(f"{k} ({v})" for k, v in per[cid].most_common(5))])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--groups", default=GROUPS)
    ap.add_argument("--audit", metavar="CONCEPT"); ap.add_argument("--n", type=int, default=20); ap.add_argument("--raw", action="store_true")
    a = ap.parse_args()
    gs = [g for g in a.groups.split(",") if os.path.isdir(os.path.join(a.repo, "corpus", g))]
    audit(a.repo, gs, a.audit, a.n, a.raw) if a.audit else main(a.repo, gs)
