#!/usr/bin/env python3
"""
best_reading.py - v33: a "best reading" for every OCR record that has at least one witness, built word by
word from the OCR and the independent witnesses already aligned by collate.py. The corpus is never edited:
the readings are an apparatus layer, and every change says which rule made it and which witnesses support it.

Why: an OCR error is rarely repeated identically by a different scan or edition (collate.py). So where the
witnesses outvote the OCR, their reading is very likely what the printed page says. Where a single witness
disagrees, it may be an OCR error or a genuine variant of another edition; the rules below only accept it
when the OCR form is not a word at all.

Rules, per word of the OCR (applied in this order; nothing else is changed):
  join      the OCR split one word in two, or ran words together, the letters are identical to a witness's
            (e.g. "الو جود" -> "الوجود"), and the change turns a non-word into attested words (witnesses are
            OCR too, so a witness's own joins such as "لماكان" are not copied).
  majority  at least two witnesses agree on the same word against the OCR, and no witness supports the OCR form.
  lexicon   one witness disagrees, no witness supports the OCR form, the OCR form is not attested in the typed
            corpus (the lexicon, < 2 occurrences), the witness form is (>= 3), and the two look alike (letter
            similarity >= 0.5, as an OCR misreading does; this guards against misaligned words).
  insert    two or more witnesses agree on words the OCR lacks at the same place (a dropped line or word).
  open      any other disagreement: the OCR word is kept and the alternatives are listed.
Nothing is ever deleted: an OCR word that no witness has stays in the reading (it is often real text that
the OCR ran together). Where the witnesses spell the chosen word differently (e.g. ولما / ؤلما, which
normalise alike), the spelling most frequent in the typed corpus is used.
Independence: a witness helps only if its errors are independent of the OCR's. For each witness the run
measures how many of the OCR's non-words (not in the lexicon, 3+ letters) it reproduces exactly. Independent
OCR witnesses reproduce about 2-20% (rare real words, coincidences); a witness at >= 40% is effectively the
same printing read by the same engine (qashani_9979 reproduces 83%), so its agreement proves nothing and
it is set aside: it neither supports nor corrects the OCR. Its page agreement pages are also dependent,
so collation levels that rest on it overstate the text (see reports/best_reading/witness_independence.tsv).
Families: two witnesses that agree with each other at >= 0.93 (median over sampled pages) are one text
published twice (futuhat_shamela and futuhat_jk, both Bulaq-derived, agree at 0.96), so they count as one
vote. Otherwise two copies of another edition would outvote the base edition's genuine readings (the base
Futuhat is Mansub's critical edition from the autograph). A majority change of an OCR form that is itself a
real word also needs the two forms to look alike (letter similarity >= 0.5), as an OCR misreading does.
Persian works (Aflaki, Shams): the lexicon is too thin for Persian prose to call a word a non-word, so only
majority and insert apply there, and independence is not judged.
The lexicon is every Arabic-script word in the typed texts (source_type typed, shamela, ganjoor, and OpenITI),
counted after textnorm.norm; it is rebuilt from the repo on each run, so the result is reproducible.

Output
  apparatus/best_reading/<work_key>.jsonl.gz   one row per record with >= 15 words and >= 1 aligned witness:
      id, reading (surface forms: the OCR's own spelling where kept, the witness's where changed; numbers,
      sigla and brackets carried through where the OCR has them),
      words, attested (share of reading words supported by >= 2 sources: OCR + a witness, or 2 witnesses),
      witnesses (aligned ids), changes [{at, ocr, reading, rule, by}], open [{at, ocr, alts}] (first 25)
  reports/best_reading/summary.tsv   per work: records, words, attested before/after, changes by rule, open
  reports/best_reading/witness_independence.tsv   per witness: OCR non-words seen, share reproduced, used
Numbers "at" are word positions in the OCR record (Arabic-script words, as in collate.py).

Usage: python3 pipeline/verify/best_reading.py --repo . [--work KEY ...] [--exclude-witness ID] [--lexicon-cache F]
       --exclude-witness is for testing (leave one witness out, then measure against it).
"""
import argparse, collections, csv, difflib, gzip, json, os, pickle, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "search")); sys.path.insert(0, HERE)
from textnorm import norm  # noqa: E402
import collate  # noqa: E402  (reuses its witness loading, pinned by md5 / sha256)

WORD = collate.WORD
K = collate.K
from textnorm import DIAC  # noqa: E402
SURF = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]{2,}")
SURF_KEY = "\x00surface"
TYPED = {"typed", "shamela", "ganjoor", "openiti"}
LEX_BAD, LEX_GOOD = 2, 3
MIN_AG = 0.5
DEPENDENT = 0.40
FAMILY = 0.93
PERSIAN_AUTHORS = {"aflaki", "shams"}


def toks(t):
    """-> [(norm_word, surface)] ; same word sequence as collate.words(t)"""
    out = []
    for piece in (t or "").split():
        ws = WORD.findall(norm(piece))
        if len(ws) == 1: out.append((ws[0], piece))
        else: out += [(w, w) for w in ws]
    return out


def toks_glue(t):
    """-> ([(norm_word, surface)], glue) ; glue[i] = the non-word pieces (numbers, sigla, brackets) before word i,
    glue[len] = those at the end, so the reading keeps them exactly where the OCR has them."""
    out, glue, g = [], [], []
    for piece in (t or "").split():
        ws = WORD.findall(norm(piece))
        if not ws: g.append(piece); continue
        if len(ws) == 1: glue.append(g); g = []; out.append((ws[0], piece))
        else:
            for w in ws: glue.append(g); g = []; out.append((w, w))
    glue.append(g)
    return out, glue


def build_lexicon(repo, cache=None):
    if cache and os.path.exists(cache): return pickle.load(open(cache, "rb"))
    idx = list(csv.DictReader(open(os.path.join(repo, "catalogs/works_index.tsv"), encoding="utf-8"), delimiter="\t"))
    paths = [r["corpus_path"] for r in idx if r["source_type"] in TYPED]
    for root, _, fs in os.walk(os.path.join(repo, "corpus/openiti")):
        paths += [os.path.relpath(os.path.join(root, f), repo) for f in fs if ".jsonl" in f]
    c = collections.Counter(); sc = collections.Counter(); t0 = time.time()
    for p in sorted(set(paths)):
        fp = os.path.join(repo, p)
        if not os.path.exists(fp): continue
        for r in collate.read_jsonl(fp):
            t = " / ".join(r["hemistichs"]) if r.get("hemistichs") else (r.get("text") or "")
            c.update(WORD.findall(norm(t))); sc.update(SURF.findall(DIAC.sub("", t)))
    for b in range(1, 7):
        for r in csv.DictReader(open(os.path.join(repo, f"corpus/mathnawi/book{b}.tsv"), encoding="utf-8"), delimiter="\t"):
            c.update(WORD.findall(norm(r["hemistich_1"] + " " + r["hemistich_2"])))
    lex = {w: n for w, n in c.items() if n >= 2}
    lex[SURF_KEY] = {w: n for w, n in sc.items() if n >= 2}
    print(f"lexicon: {len(lex)} words (>= 2 occurrences) from {len(set(paths))} typed files, {time.time() - t0:.0f}s", flush=True)
    if cache: pickle.dump(lex, open(cache, "wb"))
    return lex


class Witness(collate.Witness):
    """collate.Witness plus surface forms, and an alignment that returns the word-level opcodes."""
    def __init__(self, units):
        super().__init__(units)
        self.surf = []
        for _, t in units: self.surf += [s for _, s in toks(t)]
        if len(self.surf) != len(self.tok): self.surf = list(self.tok)

    def opcodes(self, b):
        votes = collections.Counter(); offs = collections.defaultdict(list)
        for i in range(len(b) - K + 1):
            for p in self.idx.get(" ".join(b[i:i + K]), ()):
                d = p - i; votes[d // 25] += 1; offs[d // 25].append(d)
        if not votes: return None
        bk, v = votes.most_common(1)[0]
        if v < 2: return None
        ds = sorted(offs[bk]); d0 = ds[len(ds) // 2]
        lo, hi = max(0, d0 - 30), min(len(self.tok), d0 + len(b) + 30)
        win = self.tok[lo:hi]
        sm = difflib.SequenceMatcher(None, b, win, autojunk=False)
        blocks = [x for x in sm.get_matching_blocks() if x.size]
        if not blocks: return None
        f, l = blocks[0], blocks[-1]
        ops = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "insert" and (j2 <= f.b or j1 >= l.b + l.size): continue      # outside the matched region
            if tag == "delete" and (i2 <= f.a or i1 >= l.a + l.size): tag = "outside"  # OCR words the window doesn't cover
            ops.append((tag, i1, i2, lo + j1, lo + j2))
        bs_, ws_ = "".join(b), "".join(win)  # page agreement, as in collate.py (letter 4-grams)
        bg = collections.Counter(bs_[i:i + 4] for i in range(len(bs_) - 3))
        wg = collections.Counter(ws_[i:i + 4] for i in range(len(ws_) - 3))
        return ops, sum((bg & wg).values()) / max(1, sum(bg.values()))


def families(Ws, units):
    """wid -> family id: witnesses agreeing with each other at >= FAMILY are one text."""
    fam = {w: w for w in Ws}
    ids = sorted(Ws)
    for x in range(len(ids)):
        for y in range(x + 1, len(ids)):
            a, b = ids[x], ids[y]; ag = []
            for _, t in units[a][::max(1, len(units[a]) // 200)]:
                ws = collate.words(t)
                if len(ws) < 40: continue
                r = collate.Witness.align(Ws[b], ws)
                if r: ag.append(r[0])
                if len(ag) >= 60: break
            if ag and sorted(ag)[len(ag) // 2] >= FAMILY:
                old, new = fam[b], fam[a]
                for k in fam:
                    if fam[k] == old: fam[k] = new
    return fam


def read_record(b, bs, aligned, lex, persian=False, fam=None, glue=None):
    """b/bs: OCR norm / surface words; aligned: {wid: (Witness, ops)} -> reading, stats"""
    n = len(b)
    eq = [set() for _ in range(n)]                       # witnesses that read the OCR word
    alt = [collections.defaultdict(set) for _ in range(n)]  # norm alt word -> witnesses (1:1 replacements)
    alt_s = {}                                           # (i, norm alt) -> surface
    cover = [set() for _ in range(n)]                    # witnesses whose aligned region covers position i
    joins = {}                                           # i1 -> (i2, surface words, wid)
    ins = collections.defaultdict(lambda: collections.defaultdict(set))  # before position i -> tuple(words) -> wids
    ins_s = {}
    for wid, (W, ops) in aligned.items():
        for tag, i1, i2, j1, j2 in ops:
            if tag == "outside": continue
            for i in range(i1, i2): cover[i].add(wid)
            if tag == "equal":
                for i in range(i1, i2): eq[i].add(wid)
            elif tag == "replace":
                if "".join(b[i1:i2]) == "".join(W.tok[j1:j2]) and (i2 - i1) != (j2 - j1):
                    if not persian and any(lex.get(x, 0) < LEX_BAD for x in b[i1:i2]) and all(lex.get(x, 0) >= LEX_GOOD for x in W.tok[j1:j2]):
                        joins.setdefault(i1, (i2, W.surf[j1:j2], wid))
                elif i2 - i1 == j2 - j1:
                    for k in range(i2 - i1):
                        alt[i1 + k][W.tok[j1 + k]].add(wid); alt_s.setdefault((i1 + k, W.tok[j1 + k]), []).append(W.surf[j1 + k])
            elif tag == "insert":
                key = tuple(W.tok[j1:j2]); ins[i1][key].add(wid); ins_s.setdefault((i1, key), W.surf[j1:j2])
    slex = lex.get(SURF_KEY, {})
    fam = fam or {}
    nv = lambda ws: len({fam.get(x, x) for x in ws})  # independent votes
    def pick(i, a):  # best-attested spelling among the witnesses' surface forms for norm word a
        c = alt_s[(i, a)]
        return max(c, key=lambda x: (slex.get(DIAC.sub("", x).strip("«»()[]،؛.:!؟\"'"), 0), c.count(x)))
    out, changes, opens, att = [], [], [], 0
    glue = glue or [[] for _ in range(n + 1)]
    i = 0
    while i <= n:
        out += glue[i]
        for key, ws in ins.get(i, {}).items():
            if nv(ws) >= 2 and len(key) <= 12:
                out += ins_s[(i, key)]; att += len(key)
                changes.append(dict(at=i, ocr="", reading=" ".join(ins_s[(i, key)]), rule="insert", by=sorted(ws)))
        if i == n: break
        if i in joins and not eq[i]:
            i2, sw, wid = joins[i]
            for k in range(i + 1, i2): out += glue[k]
            out += sw; att += len(sw)
            changes.append(dict(at=i, ocr=" ".join(bs[i:i2]), reading=" ".join(sw), rule="join", by=[wid])); i = i2; continue
        w = b[i]; sup = eq[i]
        best, bw = max(alt[i].items(), key=lambda x: nv(x[1]), default=(None, set()))
        if not sup and best and nv(bw) >= 2 and (lex.get(w, 0) < LEX_BAD or difflib.SequenceMatcher(None, w, best).ratio() >= 0.5):
            s_ = pick(i, best); out.append(s_); att += 1
            changes.append(dict(at=i, ocr=bs[i], reading=s_, rule="majority", by=sorted(bw)))
        elif not persian and not sup and best and nv(bw) == 1 and lex.get(w, 0) < LEX_BAD and lex.get(best, 0) >= LEX_GOOD \
                and difflib.SequenceMatcher(None, w, best).ratio() >= 0.5:
            s_ = pick(i, best); out.append(s_)
            changes.append(dict(at=i, ocr=bs[i], reading=s_, rule="lexicon", by=sorted(bw)))
        else:
            out.append(bs[i])
            if sup: att += 1
            if alt[i] and len(opens) < 25:
                opens.append(dict(at=i, ocr=bs[i], alts={pick(i, a): sorted(v) for a, v in alt[i].items()}))
        i += 1
    before = sum(1 for x in eq if x)
    nwo = len(out) - sum(len(g) for g in glue)
    return " ".join(out), dict(words=nwo, attested=round(att / max(1, nwo), 3),
                               attested_before=round(before / max(1, n), 3)), changes, opens


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    ap.add_argument("--work", action="append"); ap.add_argument("--exclude-witness", action="append", default=[])
    ap.add_argument("--lexicon-cache"); ap.add_argument("--min-agreement", type=float, default=MIN_AG); ap.add_argument("--out", help="default: <repo>/apparatus/best_reading")
    a = ap.parse_args(); repo = a.repo
    rd = lambda p: list(csv.DictReader(open(os.path.join(repo, p), encoding="utf-8"), delimiter="\t"))
    idx = {r["key"]: r for r in rd("catalogs/works_index.tsv")}
    wits = collections.defaultdict(list)
    for w in rd("catalogs/witnesses.tsv"):
        if w["witness_id"] not in a.exclude_witness: wits[w["work_key"]].append(w)
    lex = build_lexicon(repo, a.lexicon_cache)
    out_dir = a.out or os.path.join(repo, "apparatus/best_reading"); os.makedirs(out_dir, exist_ok=True)
    summ, indep = [], []
    for wk in sorted(wits):
        if a.work and wk not in a.work: continue
        if wk not in idx: print("skip (not in works_index):", wk); continue
        t0 = time.time()
        units = {w["witness_id"]: collate.witness_units(repo, w) for w in wits[wk]}
        Ws = {k: Witness(u) for k, u in units.items()}
        fam = families(Ws, units); del units
        persian = idx[wk]["source_type"] == "ganjoor" or wk.split(".")[0] in PERSIAN_AUTHORS
        recs, seen, rep_ = [], collections.Counter(), collections.Counter()
        for r in collate.read_jsonl(os.path.join(repo, idx[wk]["corpus_path"])):
            tk, gl = toks_glue(r.get("text") or r.get("text_raw"))
            if len(tk) < 15: continue
            b, bs = [x[0] for x in tk], [x[1] for x in tk]
            al = {}
            for wid, W in Ws.items():
                res = W.opcodes(b)
                if not res or res[1] < a.min_agreement: continue
                al[wid] = (W, res[0])
                for tag, i1, i2, _, _ in res[0]:
                    if tag in ("equal", "replace"):
                        for k in range(i1, i2):
                            if len(b[k]) >= 3 and lex.get(b[k], 0) < LEX_BAD:
                                seen[wid] += 1; rep_[wid] += tag == "equal"
            if al: recs.append((r["id"], b, bs, al, gl))
        used = set()
        for w in wits[wk]:
            wid = w["witness_id"]; rate = rep_[wid] / seen[wid] if seen[wid] else None
            ok = persian or rate is None or rate < DEPENDENT
            if ok: used.add(wid)
            note = "" if ok else f"reproduces {rate:.0%} of the OCR's non-words: same printing and engine"
            if fam[wid] != wid: note = (note + "; " if note else "") + f"same text as {fam[wid]}: one vote together"
            indep.append([wk, wid, w["relation"], seen[wid], "" if rate is None else round(rate, 3), "yes" if ok else "no", note])
        rules = collections.Counter(); nrec = nw = nb = n_att = n_att0 = n_open = 0
        with gzip.open(os.path.join(out_dir, f"{wk}.jsonl.gz"), "wt", encoding="utf-8", compresslevel=9) as f:
            for rid, b, bs, al, gl in recs:
                aligned = {k: v for k, v in al.items() if k in used}
                if not aligned: continue
                reading, st, ch, op = read_record(b, bs, aligned, lex, persian, {k: fam[k] for k in aligned}, gl)
                rules.update(c["rule"] for c in ch); nrec += 1; nw += st["words"]
                n_att += st["attested"] * st["words"]; n_att0 += st["attested_before"] * len(b); nb += len(b); n_open += len(op)
                f.write(json.dumps(dict(id=rid, reading=reading, witnesses=sorted(aligned), **st,
                                        changes=ch, open=op), ensure_ascii=False) + "\n")
        if not nrec: os.remove(os.path.join(out_dir, f"{wk}.jsonl.gz"))
        row = [wk, nrec, nw, round(n_att0 / max(1, nb), 3), round(n_att / max(1, nw), 3)] + \
              [rules[k] for k in ("join", "majority", "lexicon", "insert")] + [n_open, ",".join(sorted(used))]
        summ.append(row); print(*row, f"{time.time() - t0:.0f}s", sep="\t", flush=True)
    if not a.work and not a.exclude_witness:
        os.makedirs(os.path.join(repo, "reports/best_reading"), exist_ok=True)
        with open(os.path.join(repo, "reports/best_reading/summary.tsv"), "w", encoding="utf-8") as f:
            c = csv.writer(f, delimiter="\t", lineterminator="\n")
            c.writerow(["work", "records", "words", "attested_before", "attested_after", "join", "majority", "lexicon",
                        "insert", "open", "witnesses"])
            c.writerows(summ)
        with open(os.path.join(repo, "reports/best_reading/witness_independence.tsv"), "w", encoding="utf-8") as f:
            c = csv.writer(f, delimiter="\t", lineterminator="\n")
            c.writerow(["work", "witness", "relation", "ocr_nonwords_aligned", "share_reproduced", "used", "note"])
            c.writerows(indep)


if __name__ == "__main__":
    main()
