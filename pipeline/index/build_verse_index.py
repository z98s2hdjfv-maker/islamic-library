#!/usr/bin/env python3
"""
build_verse_index.py - v29: tag every passage of the commentaries with the Qur'anic verse it explains, so that
one lookup ("2:31") returns every commentator in the library.

The commentaries mark verses in different ways (Tabari quotes the verse in braces, al-Tustari uses [2.31]
headings, al-Sulami @QB@ tags, others quote without marks), so the method does not rely on marks: it recognises
the Qur'an's own words. The whole Mushaf (corpus/quran) is cut into 4-word sequences, keeping only those that
occur in at most 3 verses; a sequence found in only one verse weighs 2, otherwise 1. Reading each commentary
in order:
  - where the edition itself heads a passage with a verse number ([2.31] in its headings), that verse is taken:
    how = "heading";
  - otherwise a passage whose quotations of one verse weigh at least MIN_HITS near its start (the lemma, first 60
    words) starts that verse: how = "lemma";
  - quotations later in a passage, or of verses far from the current place (more than 20 verses back or 60 ahead
    in the same sura, or another sura), are cross-references: recorded as how = "cited", not as the current verse;
  - a passage that quotes nothing continues the current verse: how = "continues".
Collections that are not commentaries (--cite-only: Ibn Arabi, nur, wilaya, asma, al-Jilani, the Sufi manuals)
are indexed for their quotations only (how = "cited"), so a verse also returns the Sufi texts that quote it.
A new sura is accepted as the current place only from a lemma quotation of at least 2*MIN_HITS sequences.

Output (reports/index/):
  verse_index.tsv.gz   sura, aya, work, record_id, how, hits   (sorted by sura, aya, work, record order)
  verse_coverage.tsv   per work: passages, passages placed, verses reached (of 6236), share of lemma placements
Usage: python3 pipeline/index/build_verse_index.py --repo . [--works tafsir,tafsir_sufi,tafsir_ahkam]
"""
import argparse, collections, csv, glob, gzip, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from textnorm import norm  # noqa: E402

WORD = re.compile(r"[\u0621-\u063A\u0641-\u064A]+")
K, MIN_HITS, LEMMA = 4, 2, 60
HEAD = re.compile(r"\[(\d{1,3})\.(\d{1,3})\]")


def words(t):
    return WORD.findall(norm(t or ""))


def quran_index(repo):
    verses, grams = [], collections.defaultdict(set)
    for l in gzip.open(os.path.join(repo, "corpus/quran/0001Quran.Mushaf.jsonl.gz"), "rt", encoding="utf-8"):
        r = json.loads(l)
        if r.get("kind", "verse") != "verse": continue
        w = words(r["text"]); v = (r["sura"], r["aya"]); verses.append(v)
        for i in range(len(w) - K + 1): grams[" ".join(w[i:i + K])].add(v)
    return verses, {g: vs for g, vs in grams.items() if len(vs) <= 3}


def hits(ws, grams):
    """weighted: a sequence found in only one verse counts 2, in two or three verses 1"""
    c = collections.Counter()
    for i in range(len(ws) - K + 1):
        vs = grams.get(" ".join(ws[i:i + K]), ())
        for v in vs: c[v] += 2 if len(vs) == 1 else 1
    return c


def main(repo, groups, cite_groups=()):
    verses, grams = quran_index(repo)
    order = {v: i for i, v in enumerate(verses)}
    rows, cov = [], []
    for g in list(groups) + list(cite_groups):
        cite_only = g in cite_groups
        for p in sorted(glob.glob(os.path.join(repo, "corpus", g, "*.jsonl*"))):
            work = f"{g}.{os.path.basename(p).split('.jsonl')[0]}"
            op = gzip.open if p.endswith(".gz") else open
            cur, n, placed, lemma, reached = None, 0, 0, 0, set()
            with op(p, "rt", encoding="utf-8") as f:
                for l in f:
                    r = json.loads(l); n += 1
                    ws = words(r.get("text") or r.get("text_raw"))
                    if not ws: continue
                    head, rest = hits(ws[:LEMMA], grams), hits(ws[LEMMA:], grams)
                    new = None
                    m = HEAD.findall(" ".join(r.get("headings") or []))
                    if m and (int(m[-1][0]), int(m[-1][1])) in order:
                        new = ((int(m[-1][0]), int(m[-1][1])), 99)  # the edition's own verse heading
                    elif head:
                        v, h = max(head.items(), key=lambda x: (x[1], -order[x[0]]))
                        near = cur and v[0] == cur[0] and -20 <= order[v] - order[cur] <= 60
                        if h >= MIN_HITS and (near or h >= 2 * MIN_HITS or cur is None): new = (v, h)
                    for v, h in (head + rest).items():
                        if h >= MIN_HITS and (not new or v != new[0]):
                            rows.append((v[0], v[1], work, r.get("id", ""), "cited", h))
                    if cite_only:
                        if new: rows.append((new[0][0], new[0][1], work, r.get("id", ""), "cited", new[1]))
                        continue
                    if new:
                        cur = new[0]; lemma += 1
                        rows.append((cur[0], cur[1], work, r.get("id", ""), "heading" if new[1] == 99 else "lemma", new[1]))
                    elif cur:
                        rows.append((cur[0], cur[1], work, r.get("id", ""), "continues", 0))
                    if new or cur: placed += 1; reached.add(cur)
            cov.append([work, n, placed, len(reached), round(100 * lemma / max(placed, 1), 1)])
            print(*cov[-1], sep="\t", flush=True)
    out = os.path.join(repo, "reports/index"); os.makedirs(out, exist_ok=True)
    rows.sort(key=lambda x: (x[0], x[1], x[2]))
    with gzip.open(os.path.join(out, "verse_index.tsv.gz"), "wt", encoding="utf-8", compresslevel=9) as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["sura", "aya", "work", "record_id", "how", "hits"]); w.writerows(rows)
    with open(os.path.join(out, "verse_coverage.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["work", "passages", "placed", "verses_reached", "pct_lemma"]); w.writerows(cov)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    ap.add_argument("--works", default="tafsir,tafsir_sufi,tafsir_ahkam")
    ap.add_argument("--cite-only", default="ibnarabi,nur,wilaya,asma,jilani,sufi_manuals,tafsir_sufi_extra,afterlife,grading,modern",
                    help="collections that are not commentaries: only their quotations are indexed (how = cited)")
    a = ap.parse_args()
    main(a.repo, a.works.split(","), [g for g in a.cite_only.split(",") if os.path.isdir(os.path.join(a.repo, "corpus", g))])
