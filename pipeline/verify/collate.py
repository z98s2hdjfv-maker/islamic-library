#!/usr/bin/env python3
"""
collate.py - v22: collate the library's OCR texts against independent free witnesses, and overlay the
result with OCR triage and the verification log into one confidence table per record.

Why: an OCR error is rarely repeated identically by a different scan or a different edition. Where two
independent witnesses agree, the reading is corroborated (the logic of mutaba'at in hadith criticism);
where they disagree, the passage needs a human eye, the scan, or a printed edition. The corpus is never
edited: this only writes reports.

catalogs/witnesses.tsv   one row per witness of a base work:
  work_key   base work (works_index key) whose records are checked
  witness_id short id
  kind       corpus  (a file already in the repo; source = its path)
             archive (archive.org OCR; source = item id; files = file bases joined by " || ";
                      md5 = "text,index" md5 pairs joined by " || "; pinned: a changed file stops the build)
             openiti (source = raw URL; sha256 pinned)
  relation   same_edition_rescan | other_edition | other_edition_typed
             (a rescan checks OCR only; another edition also shows genuine textual variants, so a
             divergence there is "differs", not "wrong")
Witness files are cached byte-exact in sources/witnesses/<work_key>/<witness_id>/.

Method: both texts are normalised (pipeline/search/textnorm.py), reduced to Arabic-script words, and
each base record is placed in the witness by voting on shared 5-word shingles; the matched window is
compared. agreement = share of the record's 4-letter sequences (spaces removed, so OCR word-splitting and
joining do not count as errors) also found in the matched witness window; word_agreement = share of its
whole words found in order in the window (difflib). The listed differences are word-level.

Output (reports/collation/):
  summary.tsv            per work and witness: records aligned, mean agreement, % corroborated / divergent
  records.tsv.gz         per record and witness: agreement, witness locator, up to 6 differing spans
  confidence.tsv.gz      per record: OCR score, best agreement, verification status, and a level:
                         verified   - checked by a person or against the scan (catalogs/verification_log.tsv)
                         corroborated - agreement >= 0.85 with at least one witness
                         partial    - 0.60-0.85 (read the listed differences)
                         divergent  - < 0.60   (check the scan or a printed edition)
                         Calibration: two clean typeset scans of the same text score about 0.87-0.92, since
                         one wrong letter breaks up to four 4-letter sequences and page furniture (running
                         heads, editors' footnotes) differs between editions.
                         unmatched  - no witness passage found (lacuna, different recension, or heavy noise)
                         no_witness - the work has no witness yet
  confidence_summary.tsv per work: records by level
Usage: python3 pipeline/verify/collate.py --repo .
"""
import argparse, collections, csv, difflib, gzip, hashlib, json, os, re, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from textnorm import norm  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_quality import score as ocr_score  # noqa: E402

WORD = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]{2,}")
K = 5


def words(t):
    return WORD.findall(norm(t or ""))


def get(url, check=None, kind="md5"):
    for a in range(5):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "islamic-library"}), timeout=300).read()
            if check and getattr(hashlib, kind)(raw).hexdigest() != check:
                raise SystemExit(f"{kind} mismatch for {url}: source changed, re-pin catalogs/witnesses.tsv")
            return raw
        except SystemExit:
            raise
        except Exception as e:
            print("retry", url, e, flush=True); time.sleep(5 * (a + 1))
    raise SystemExit(f"could not download {url}")


def cached(repo, w, name, url, check, kind="md5"):
    d = os.path.join(repo, "sources/witnesses", w["work_key"], w["witness_id"]); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, re.sub(r"[^\w.-]", "_", name))
    if os.path.exists(p):
        raw = open(p, "rb").read()
        if not check or getattr(hashlib, kind)(raw).hexdigest() == check: return raw
    raw = get(url, check, kind); open(p, "wb").write(raw); return raw


def read_jsonl(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f:
        for l in f: yield json.loads(l)


def locator(r):
    return " ".join(f"{k}={r[k]}" for k in ("vol", "page", "page_before", "part", "leaf", "printed_page") if r.get(k) not in (None, ""))


def witness_units(repo, w):
    """-> list of (locator, text) in reading order"""
    if w["kind"] == "corpus":
        return [(r.get("id", ""), r.get("text") or r.get("text_raw") or "") for r in read_jsonl(os.path.join(repo, w["source"]))]
    if w["kind"] == "openiti":
        raw = cached(repo, w, "text", w["source"], w["md5"], "sha256").decode("utf-8")
        body = raw.split("#META#Header#End#", 1)[-1]; units, page = [], ""
        for part in re.split(r"(PageV\d+P\d+)", body):
            if part.startswith("PageV"): page = part; continue
            units.append((page, part))
        return units
    units = []
    for base, pair in zip(w["files"].split(" || "), w["md5"].split(" || ")):
        m_text, m_index = pair.split(",")
        q = lambda s: f"https://archive.org/download/{w['source']}/{urllib.parse.quote(base + s)}"
        text = gzip.decompress(cached(repo, w, base + "_hocr_searchtext.txt.gz", q("_hocr_searchtext.txt.gz"), m_text)).decode("utf-8")
        index = json.loads(gzip.decompress(cached(repo, w, base + "_hocr_pageindex.json.gz", q("_hocr_pageindex.json.gz"), m_index)))
        tag = "" if " || " not in w["files"] else base[-12:] + " "
        for leaf, (s0, e0, *_r) in enumerate(index, 1): units.append((f"{tag}leaf={leaf}", text[s0:e0]))
    return units


class Witness:
    def __init__(self, units):
        self.tok, self.loc = [], []
        for loc, t in units:
            ws = words(t); self.tok += ws; self.loc += [loc] * len(ws)
        cnt = collections.Counter(); self.idx = {}
        for i in range(len(self.tok) - K + 1):
            h = " ".join(self.tok[i:i + K]); cnt[h] += 1
            if cnt[h] <= 4: self.idx.setdefault(h, []).append(i)
        for h, c in cnt.items():
            if c > 4: self.idx.pop(h, None)

    def align(self, b):
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
        blocks = sm.get_matching_blocks(); matched = sum(x.size for x in blocks)
        first = next((x for x in blocks if x.size), None); last = next((x for x in reversed(blocks) if x.size), None)
        wl = (self.loc[lo + first.b], self.loc[lo + last.b + last.size - 1]) if first else ("", "")
        diffs = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal": continue
            if first and (j2 <= first.b or j1 >= last.b + last.size) and tag == "insert": continue
            diffs.append(f"{' '.join(b[i1:i2][:6]) or '∅'} → {' '.join(win[j1:j2][:6]) or '∅'}")
        bs, ws = "".join(b), "".join(win)  # letters only: robust to OCR word-splitting and joining
        bg = collections.Counter(bs[i:i + 4] for i in range(len(bs) - 3))
        wg = collections.Counter(ws[i:i + 4] for i in range(len(ws) - 3))
        return sum((bg & wg).values()) / max(1, sum(bg.values())), matched / len(b), wl, diffs


def main(repo):
    rd = lambda p: list(csv.DictReader(open(os.path.join(repo, p), encoding="utf-8"), delimiter="\t"))
    idx = {r["key"]: r for r in rd("catalogs/works_index.tsv")}
    wits = collections.defaultdict(list)
    for w in rd("catalogs/witnesses.tsv"): wits[w["work_key"]].append(w)
    vlog = {r["record_id"]: r["status"] for r in rd("catalogs/verification_log.tsv")} if os.path.exists(os.path.join(repo, "catalogs/verification_log.tsv")) else {}
    targets = [k for k, r in idx.items() if r["source_type"] == "ocr_uncorrected"] + [k for k in wits if k not in idx or idx[k]["source_type"] != "ocr_uncorrected"]
    out = os.path.join(repo, "reports/collation"); os.makedirs(out, exist_ok=True)
    summ, lvl_summ = [], []
    rec_f = gzip.open(os.path.join(out, "records.tsv.gz"), "wt", encoding="utf-8", compresslevel=6)
    con_f = gzip.open(os.path.join(out, "confidence.tsv.gz"), "wt", encoding="utf-8", compresslevel=6)
    rw, cw = csv.writer(rec_f, delimiter="\t", lineterminator="\n"), csv.writer(con_f, delimiter="\t", lineterminator="\n")
    rw.writerow(["work", "record_id", "locator", "witness", "relation", "agreement", "word_agreement", "witness_from", "witness_to", "n_diffs", "diffs"])
    cw.writerow(["work", "record_id", "locator", "ocr_score", "best_agreement", "best_witness", "verification", "level"])
    for wk in sorted(set(targets)):
        if wk not in idx: print("skip (not in works_index):", wk); continue
        base = [r for r in read_jsonl(os.path.join(repo, idx[wk]["corpus_path"]))]
        best = {}
        for w in wits.get(wk, []):
            t0 = time.time(); W = Witness(witness_units(repo, w)); ag = []
            for r in base:
                b = words(r.get("text") or r.get("text_raw"))
                if len(b) < 15: continue
                res = W.align(b)
                if not res: rw.writerow([wk, r.get("id"), locator(r), w["witness_id"], w["relation"], "", "", "", "", "", "unmatched"]); continue
                a, aw, (wf, wt), diffs = res; ag.append(a)
                rw.writerow([wk, r.get("id"), locator(r), w["witness_id"], w["relation"], f"{a:.3f}", f"{aw:.3f}", wf, wt, len(diffs), " | ".join(diffs[:6])])
                if a > best.get(r.get("id"), (-1, ""))[0]: best[r.get("id")] = (a, w["witness_id"])
            n = sum(1 for r in base if len(words(r.get("text") or r.get("text_raw"))) >= 15)
            summ.append([wk, w["witness_id"], w["relation"], n, len(ag), round(100 * len(ag) / max(n, 1), 1),
                         round(sum(ag) / len(ag), 3) if ag else "", round(100 * sum(a >= .85 for a in ag) / max(n, 1), 1),
                         round(100 * sum(a < .6 for a in ag) / max(n, 1), 1)])
            print(*summ[-1], f"{time.time() - t0:.0f}s", sep="\t", flush=True)
        lv = collections.Counter()
        for r in base:
            b = words(r.get("text") or r.get("text_raw"))
            if len(b) < 15: continue
            rid = r.get("id"); s = ocr_score(r.get("text") or r.get("text_raw")); a, wid = best.get(rid, (None, ""))
            v = vlog.get(rid, "")
            level = ("verified" if v in ("verified", "corrected") else "no_witness" if not wits.get(wk) else
                     "unmatched" if a is None else "corroborated" if a >= .85 else "partial" if a >= .6 else "divergent")
            lv[level] += 1
            cw.writerow([wk, rid, locator(r), "" if s is None else s, "" if a is None else f"{a:.3f}", wid, v, level])
        lvl_summ.append([wk, sum(lv.values())] + [lv[k] for k in ("verified", "corroborated", "partial", "divergent", "unmatched", "no_witness")])
    rec_f.close(); con_f.close()
    with open(os.path.join(out, "summary.tsv"), "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n")
        c.writerow(["work", "witness", "relation", "records", "aligned", "pct_aligned", "mean_agreement", "pct_corroborated_ge85", "pct_divergent_lt60"])
        c.writerows(summ)
    with open(os.path.join(out, "confidence_summary.tsv"), "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n")
        c.writerow(["work", "records", "verified", "corroborated", "partial", "divergent", "unmatched", "no_witness"])
        c.writerows(lvl_summ)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); main(ap.parse_args().repo)
