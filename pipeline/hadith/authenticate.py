#!/usr/bin/env python3
"""
authenticate.py - v43: one command to test a saying attributed to the Prophet, a Companion or a master.

Give it a saying in Arabic. In one pass it returns, with record ids to cite:

  1. FOUND IN THE COLLECTIONS  the hadith layer (apparatus/hadith, 21 collections since v46) matched by LOOSE wording, so a
                               paraphrase or a different version is still found; with narrator, the printed number
                               where the layer has one, the grades found in the sources (the compiler's own, and
                               al-Dhahabi on al-Hakim), parallels in other collections, and the narrators of the chain
                               that are linked to Ibn Hajar's Taqrib.
  2. THE CLASSICAL CRITICS     every passage quoting the saying in the works listed in
                               catalogs/authentication_works.tsv (fabrication collections, grading works, takhrij,
                               narrator criticism), oldest author first, with the verdict words found near the quote.
  3. MODERN GRADES             the same for the modern layer (al-Albani), kept apart: never merge a modern grade into
                               a classical verdict.

Matching. Both the saying and the texts are normalised (textnorm.norm), proclitics (و ف ب ل ك ال) are stripped and
very common words dropped. A text matches when a short stretch of it holds most of the saying's remaining words:
score = 0.7 x share of the saying's words present + 0.3 x share of its adjacent word pairs kept in order.
Default threshold 0.7. A saying with fewer than three distinctive words is too short to match loosely: use
textsearch.py for it.

v44. Each hadith found also shows the later critics' verdicts joined to it as data (al-Busiri on Ibn Maja,
al-Haythami on Ahmad and al-Tabarani, al-Dhahabi on al-Hakim), each with the record to cite and marked as a verdict
on the CHAIN or on the hadith; al-Albani on al-Tirmidhi as MODERN, apart; and a note when the same wording is also in
al-Bukhari or Muslim. The critics' numbered entries on the saying (apparatus/sayings) are listed with their verdict.

What this is NOT. It gathers evidence; it does not grade. "Verdict words" are words found near the quote (موضوع،
لا أصل له، ضعيف، صحيح ...): they may be about another report or a narrator, so read the passage before citing it.
The chain line lists only narrators that could be linked; it ignores unlinked names, breaks in the chain, hidden
defects and corroboration. "Not found" means not found in this library by this wording: say exactly that.

  python3 pipeline/hadith/authenticate.py "اطلبوا العلم ولو بالصين"
  python3 pipeline/hadith/authenticate.py "كنت كنزا مخفيا فأحببت أن أعرف" "اختلاف أمتي رحمة"   # several, ONE pass
  python3 pipeline/hadith/authenticate.py "..." --limit 3 --context 60      # shorter output
  python3 pipeline/hadith/authenticate.py "..." --also sufi_manuals,tafsir  # also show who QUOTES it there
  python3 pipeline/hadith/authenticate.py "..." --json                      # data, e.g. for a sijill entry
"""
import argparse, collections, csv, glob, gzip, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "search"))
from textnorm import norm  # noqa: E402
from pages import segments, MARK  # noqa: E402

WORD = re.compile(r"[ء-ي]+")
NEW_ENTRY = re.compile(r"^\s*\d+\s*[-–]?\s*حديث\b")
PROCLITIC = re.compile(r"^(?:[وف])?(?:[بل])?(?:ال|ل)?(?=.{3,}$)")
STOP = set("""من في علي عن ان الا ما لا الي هو هي هذا هذه ذلك التي الذي قال قالت يقول رسول الله صلي عليه وسلم النبي
او ثم قد لم لن اذا اذ كان كانت يا ايها له لها به بها فيه فيها منه منها عنه رضي تعالي عز وجل حتي بين كل انه انها
لي لك لكم لهم هم انا انت نحن اني اي ولا وما حدثنا اخبرنا""".split())

VERDICTS = [
    ("fabricated", r"موضوع|مكذوب|مختلق|كذب\b|وضعه|من وضع|لا اصل له|لا يعرف له اصل|ليس له اصل|لا اصل لها|باطل"),
    ("very weak", r"ضعيف جدا|واه\b|واهي|متروك|منكر|ساقط|لا يصح|لا يثبت|لم يصح|غير ثابت|ليس بثابت|ليس بصحيح"),
    ("weak", r"ضعيف|الضعيف|ضعفه|ضعفوه|فيه ضعف|اسناده ضعيف|سنده ضعيف|لين\b|فيه مقال|معلول|مرسل|منقطع|مجهول|فيه من لم اعرفه"),
    ("not the Prophet's words", r"من كلام|ليس بحديث|ليس من كلام النبي|موقوف|لم اقف عليه|لا اعرفه|لم اجده|لم اره"),
    ("fair", r"حسن|حسنه|حديث حسن|اسناده جيد|سنده جيد|لا باس به|رجاله موثقون|صالح"),
    ("sound", r"صحيح|الصحيح|صححه|رجاله ثقات|رجاله رجال الصحيح|متفق عليه|اخرجه البخاري|اخرجه مسلم|رواه البخاري|رواه مسلم|ثابت"),
    ("mass-transmitted", r"متواتر"),
]
VERDICTS = [(k, re.compile(r"(?<![ء-ي])[وف]?(?:" + p.replace(r"\b", "") + r")(?![ء-ي])")) for k, p in VERDICTS]
COLL = {"0241IbnHanbal.Musnad": ("Ahmad, Musnad", 241), "0255CabdAllahDarimi.Sunan": ("al-Darimi, Sunan", 255),
        "0256Bukhari.Sahih": ("al-Bukhari, Sahih", 256), "0261Muslim.Sahih": ("Muslim, Sahih", 261),
        "0273IbnMaja.Sunan": ("Ibn Maja, Sunan", 273), "0275AbuDawudSijistani.Sunan": ("Abu Dawud, Sunan", 275),
        "0279Tirmidhi.Sunan": ("al-Tirmidhi, Sunan", 279), "0303Nasai.SunanKubra": ("al-Nasaʾi, al-Sunan al-kubra", 303),
        "0303Nasai.SunanSughra": ("al-Nasaʾi, al-Mujtaba", 303),
        "0311IbnKhuzaymaNaysaburi.Sahih": ("Ibn Khuzayma, Sahih", 311),
        "0360Tabarani.MucjamKabir": ("al-Tabarani, al-Muʿjam al-kabir", 360),
        "0385Daraqutni.Sunan": ("al-Daraqutni, Sunan", 385), "0405HakimNaysaburi.Mustadrak": ("al-Hakim, Mustadrak", 405),
        # v46
        "0204AbuDawudTayalisi.Musnad": ("al-Tayalisi, Musnad", 204), "0219IbnZubayrHumaydi.Musnad": ("al-Humaydi, Musnad", 219),
        "0292AbuBakrBazzar.BahrZakhkhar": ("al-Bazzar, Musnad", 292), "0307AbuYaclaMawsili.Musnad": ("Abu Yaʿla, Musnad", 307),
        "0739CalaDinIbnBalban.Ihsan": ("Ibn Hibban, Sahih (al-Ihsan)", 354),
        "0360Tabarani.MucjamAwsat": ("al-Tabarani, al-Muʿjam al-awsat", 360), "0360Tabarani.MucjamSaghir": ("al-Tabarani, al-Muʿjam al-saghir", 360),
        "0458Bayhaqi.ShucabIman": ("al-Bayhaqi, Shuʿab al-iman", 458)}


def stem(w):
    """a normalised word without proclitics (و ف ب ل ال) and without a final alif (كنزا = كنز, خلقا = خلق)"""
    w = PROCLITIC.sub("", w)
    return w[:-1] if len(w) >= 4 and w.endswith("ا") else w


def stems(text):
    return [stem(w) for w in WORD.findall(norm(text))]


STOP |= {stem(w) for w in STOP}


class Saying:
    def __init__(self, text):
        self.text = text
        allw = stems(text)
        self.shown = [w for w in WORD.findall(norm(text)) if stem(w) not in STOP] or WORD.findall(norm(text))
        content = [w for w in allw if w not in STOP]
        self.words = content if len(content) >= 2 else allw
        self.set = set(self.words)
        self.pairs = [(a, b) for a, b in zip(self.words, self.words[1:]) if a != b]
        self.window = max(10, 3 * len(allw))
        self.short = len(self.set) < 3
        self.need = max(1, math.ceil(0.5 * len(self.set)))

    def maybe(self, normed):
        """cheap pre-check on normalised text: enough of the words occur at all (as substrings)."""
        n = 0
        for w in self.set:
            if w in normed:
                n += 1
                if n >= self.need: return True
        return False

    def score(self, toks):
        """best stretch of `toks` (stems): -> (score, start, end) or (0, 0, 0)"""
        pos = [(i, t) for i, t in enumerate(toks) if t in self.set]
        if len({t for _, t in pos}) < self.need: return 0.0, 0, 0
        best = (0.0, 0, 0); j = 0; cnt = collections.Counter()
        for k, (i, t) in enumerate(pos):
            cnt[t] += 1
            while i - pos[j][0] >= self.window:
                cnt[pos[j][1]] -= 1
                if not cnt[pos[j][1]]: del cnt[pos[j][1]]
                j += 1
            cov = len(cnt) / len(self.set)
            if cov + 0.3 <= best[0]: continue
            seq = pos[j:k + 1]; ok = 0
            for a, b in self.pairs:
                ia = [p for p, t2 in seq if t2 == a]; ib = [p for p, t2 in seq if t2 == b]
                if any(0 < y - x <= 3 for x in ia for y in ib): ok += 1
            s = 0.7 * cov + 0.3 * (ok / len(self.pairs) if self.pairs else cov)
            if s > best[0]: best = (s, pos[j][0], i)
        return best


def opener(path):
    return gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8")


def excerpt(raw, saying, ctx):
    """the stretch of the raw text around the best match, +- ctx words"""
    ws = raw.split()
    st = [stem(x) for x in (("".join(WORD.findall(norm(w))) or "-") for w in ws)]
    s, a, b = saying.score(st)
    if not s: return " ".join(ws[:2 * ctx])
    lo, hi = max(0, a - ctx), min(len(ws), b + 1 + ctx)
    return ("… " if lo else "") + " ".join(ws[lo:hi]) + (" …" if hi < len(ws) else "")


def cues(raw, saying, before=15, after=50):
    """verdict words near the match (a verdict usually follows the quote)"""
    ws = raw.split()
    st = [stem(x) for x in (("".join(WORD.findall(norm(w))) or "-") for w in ws)]
    s, a, b = saying.score(st)
    near = norm(" ".join(ws[max(0, a - before):b + 1 + after])) if s else norm(raw)
    out = []
    for name, pat in VERDICTS:
        found = sorted(set(m.group(0) for m in pat.finditer(near)))
        if found: out.append((name, found[:4]))
    return out


def page_of(rec, saying):
    if isinstance(rec.get("page_before"), int):
        if not rec.get("vol") and not rec["page_before"] and not MARK.search(rec.get("text_raw") or ""):
            return "(no page in this source text)"
        for v, p, t in segments(rec):
            if saying.score(stems(t))[0] >= 0.5: return f"{v}:{p}" if v is not None else f"p. {p}"
        return f"{rec.get('vol')}:{rec['page_before'] + 1}ff"
    bits = [f"{k}={rec[k]}" for k in ("vol", "page", "leaf", "printed_page", "number") if rec.get(k) not in (None, "")]
    return " ".join(bits)


def scan_hadith(repo, sayings, thr):
    hits = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(repo, "apparatus/hadith/*.jsonl.gz"))):
        with opener(f) as fh:
            for line in fh:
                cand = None
                for qi, q in enumerate(sayings):
                    if cand is None:
                        r = json.loads(line); body = r.get("matn") or ""
                        full = (r.get("isnad") or "") + " " + body
                        cand = (norm(full), None)
                    if not q.maybe(cand[0]): continue
                    toks = stems(body) if body else stems(full)
                    s = q.score(toks)[0]
                    if s < thr and body:      # the split may have put the wording in the isnad part
                        s = max(s, q.score(stems(full))[0])
                    if s >= thr: hits[qi].append((s, r))
    return hits


def scan_works(repo, works, sayings, thr, follow=2):
    """-> hits[qi] = [(score, work, record, raw, following_text)]. Works like al-Maqasid al-hasana give the saying as
    a short entry heading and the verdict in the next paragraphs, so a short matching record takes the text of the
    next `follow` records with it."""
    hits = collections.defaultdict(list)
    for w in works:
        path = os.path.join(repo, w["corpus_path"])
        if not os.path.exists(path): continue
        pending = []                                   # [hit, records still to attach]
        with opener(path) as fh:
            for line in fh:
                try: r = json.loads(line)
                except ValueError: continue
                raw = r.get("text_raw") if isinstance(r.get("text_raw"), str) else r.get("text")
                if not isinstance(raw, str) or r.get("kind") == "heading": continue
                if NEW_ENTRY.match(raw): pending = []      # the next numbered entry: the verdict text has ended
                for h in pending:
                    h[0][4] = (h[0][4] + " " + raw).strip(); h[1] -= 1
                pending = [h for h in pending if h[1] > 0]
                n = norm(raw)
                for qi, q in enumerate(sayings):
                    if not q.maybe(n): continue
                    s = q.score(stems(raw))[0]
                    if s >= thr:
                        hit = [s, w, r, raw, ""]
                        hits[qi].append(hit)
                        if len(raw.split()) < 40: pending.append([hit, follow])
    return hits


def load_side(repo, ids):
    """parallels, chains, al-Dhahabi's verdicts for the matched hadith ids"""
    par, group_members, chains, dhahabi = {}, collections.defaultdict(list), {}, {}
    p = os.path.join(repo, "apparatus/hadith_links/parallels.tsv.gz")
    if os.path.exists(p):
        rows = list(csv.DictReader(opener(p), delimiter="\t"))
        for r in rows:
            if r["hadith_id"] in ids: par[r["hadith_id"]] = r["group"]
        want = set(par.values())
        for r in rows:
            if r["group"] in want: group_members[r["group"]].append(r["hadith_id"])
    p = os.path.join(repo, "apparatus/hadith_links/chains.jsonl.gz")
    if os.path.exists(p):
        with opener(p) as fh:
            for line in fh:
                m = re.match(r'\{"hadith_id": "([^"]+)"', line)
                if m and m.group(1) in ids: chains[m.group(1)] = json.loads(line)
    p = os.path.join(repo, "apparatus/hadith_grades/dhahabi_talkhis_mustadrak.tsv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
            if r["hadith_id"] in ids: dhahabi[r["hadith_id"]] = r
    # v44: the later critics' verdicts as data (build_critic_grades.py); modern ones from their own folder
    critics = collections.defaultdict(list)
    for folder in ("apparatus/hadith_grades", "apparatus/hadith_grades_modern"):
        for p in sorted(glob.glob(os.path.join(repo, folder, "*.tsv"))):
            with open(p, encoding="utf-8") as fh:
                rd = csv.DictReader(fh, delimiter="\t")
                if "critic" not in (rd.fieldnames or []): continue
                for r in rd:
                    if r["hadith_id"] in ids: critics[r["hadith_id"]].append(r)
    insahih = {}
    p = os.path.join(repo, "apparatus/hadith_links/in_sahih.tsv.gz")
    if os.path.exists(p):
        for r in csv.DictReader(opener(p), delimiter="\t"):
            if r["hadith_id"] in ids: insahih[r["hadith_id"]] = r
    dhahabi["__critics__"], dhahabi["__insahih__"] = critics, insahih
    return par, group_members, chains, dhahabi


def hadith_entry(score, r, par, members, chains, dhahabi, q, ctx):
    name, death = COLL.get(r["collection"], (r["collection"], None))
    e = {"id": r["id"], "collection": name, "death_ah": death, "score": round(score, 2),
         "number": r.get("number"), "numbering": r.get("numbering"),
         "printed_numbers": r.get("edition_numbers") or [], "narrator": r.get("narrator"), "caliph": r.get("caliph"),
         "grades_classical": [{"by": g.get("by"), "grade": g.get("grade")} for g in r.get("grades") or []],
         "text": excerpt(r.get("matn") or r.get("isnad") or "", q, ctx), "source_ids": r.get("source_ids"),
         "compiler_remark": (r.get("comments") or [])[:1] if r["collection"] in ("0292AbuBakrBazzar.BahrZakhkhar", "0360Tabarani.MucjamAwsat", "0360Tabarani.MucjamSaghir") else []}
    if r["id"] in dhahabi and not any(g["by"] == "al-Dhahabi" for g in e["grades_classical"]):
        e["grades_classical"].append({"by": "al-Dhahabi (Talkhis)", "grade": dhahabi[r["id"]]["verdict"],
                                      "record": dhahabi[r["id"]]["talkhis_record"]})
    e["grades_modern"] = []
    for v in sorted(dhahabi.get("__critics__", {}).get(r["id"], []), key=lambda v: int(v["death_ah"] or 9999)):
        row = {"by": v["critic"], "grade": v["verdict"], "scope": v["scope"], "class": v["class"],
               "record": v["critic_record"], "loc": v["loc"], "match": v["match"], "candidates": int(v["candidates"] or 1)}
        (e["grades_modern"] if v["layer"] == "modern" else e["grades_classical"]).append(row)
    if any("(his own remark)" in g["by"] for g in e["grades_classical"]): e["compiler_remark"] = []      # v47: it is in the table
    s = dhahabi.get("__insahih__", {}).get(r["id"])
    if s:
        e["wording_also_in_sahih"] = [x for x in (s["bukhari"] + ";" + s["muslim"]).split(";") if x]
        e["wording_also_in_sahih_companion"] = s.get("companion") or ""          # v47: same | other | unknown
        if s.get("critic_record"): e["critic_says_in_sahih"] = s["critic_record"]
    g = par.get(r["id"])
    if g:
        cols = sorted({m.split(":")[2] for m in members[g]})
        e["parallel_group"] = g
        e["parallel_collections"] = [COLL.get(c, (c,))[0] for c in cols]
        e["agreed_upon_by_wording"] = {"0256Bukhari.Sahih", "0261Muslim.Sahih"} <= set(cols)
    c = chains.get(r["id"])
    if c:
        e["chain"] = {"names": c.get("names"), "linked": c.get("linked"),
                      "narrators": [{"name": n["name"], "grade": n.get("grade"), "taqrib_no": n.get("taqrib_no")}
                                    for n in c.get("narrators", [])],
                      "weakest_linked": c.get("weakest_rank_name")}
    return e


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("saying", nargs="+", help="one or more sayings in Arabic; all are tested in ONE pass")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--threshold", type=float, default=0.7, help="match score needed, 0-1 (default 0.7)")
    ap.add_argument("--limit", type=int, default=5, help="passages shown per section (default 5)")
    ap.add_argument("--context", type=int, default=40, help="words of context around a quote (default 40)")
    ap.add_argument("--also", default="", help="extra corpus folders to show who quotes the saying (e.g. tafsir,sira)")
    ap.add_argument("--no-modern", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    sayings = [Saying(s) for s in a.saying]
    works = list(csv.DictReader(open(os.path.join(a.repo, "catalogs/authentication_works.tsv"), encoding="utf-8"),
                                delimiter="\t"))
    if a.no_modern: works = [w for w in works if w["layer"] != "modern"]
    listed = {w["corpus_path"] for w in works}
    for folder in [f for f in a.also.split(",") if f]:
        for p in sorted(glob.glob(os.path.join(a.repo, "corpus", folder, "*.jsonl*"))):
            rel = os.path.relpath(p, a.repo)
            stem = os.path.basename(p).split(".jsonl")[0]
            if rel in listed or any(os.path.basename(x).startswith(stem) for x in listed): continue
            m = re.match(r"(\d{4})([A-Za-z]+)\.(\w+)", stem)
            works.append({"corpus_path": rel, "function": "quotes", "layer": "also", "author": m.group(2) if m else folder,
                          "work": m.group(3) if m else stem, "death_ah": str(int(m.group(1))) if m else "", "note": ""})
    hh = scan_hadith(a.repo, sayings, a.threshold)
    wh = scan_works(a.repo, works, sayings, a.threshold)
    ids = {r["id"] for v in hh.values() for _, r in v}
    par, members, chains, dhahabi = load_side(a.repo, ids)

    table = []
    tp = os.path.join(a.repo, "apparatus/sayings/sayings.tsv.gz")
    if os.path.exists(tp):
        for r in csv.DictReader(opener(tp), delimiter="\t"): table.append((stems(r["saying"]), r))
    table_modern = []
    tp = os.path.join(a.repo, "apparatus/sayings/sayings_modern.tsv.gz")
    if os.path.exists(tp) and not a.no_modern:
        for r in csv.DictReader(opener(tp), delimiter="\t"): table_modern.append((stems(r["saying"]), r))
    out = []
    for qi, q in enumerate(sayings):
        H = sorted(hh.get(qi, []), key=lambda x: (-x[0], COLL.get(x[1]["collection"], ("", 9999))[1]))
        seen = collections.Counter(); ranked = []
        for x in H:                      # the best match of each collection first, oldest collection first
            ranked.append((seen[x[1]["collection"]], COLL.get(x[1]["collection"], ("", 9999))[1], -x[0], len(ranked), x))
            seen[x[1]["collection"]] += 1
        H = [t[-1] for t in sorted(ranked, key=lambda t: t[:4])]
        res = {"saying": q.text, "words_matched_on": q.shown, "too_short_for_loose_match": q.short,
               "collections_searched": len(glob.glob(os.path.join(a.repo, "apparatus/hadith/*.jsonl.gz"))),
               "hadith": [hadith_entry(s, r, par, members, chains, dhahabi, q, a.context) for s, r in H],
               "critics": [], "collection": [], "modern": [], "also": [],
               "entries": sorted(({"saying_id": r["saying_id"], "group": r["group"], "critic": r["critic"],
                                   "death_ah": r["death_ah"], "work": r["work"], "entry": r["entry"],
                                   "saying": r["saying"], "verdict": r["verdict"], "cues": r["cues"],
                                   "record": r["record"], "loc": r["loc"]}
                                  for st, r in table if q.score(st)[0] >= a.threshold),
                                 key=lambda e: int(e["death_ah"])),
               "entries_modern": [{"saying_id": r["saying_id"], "critic": r["critic"], "work": r["work"], "entry": r["entry"],
                                   "saying": r["saying"], "verdict": r["verdict"], "record": r["record"]}
                                  for st, r in table_modern if q.score(st)[0] >= a.threshold]}
        W = sorted(wh.get(qi, []), key=lambda x: (int(x[1]["death_ah"] or 9999), -x[0]))
        for s, w, r, raw, nxt in W:
            res["critics" if w["layer"] == "classical" else w["layer"]].append(
                {"id": r.get("id"), "author": w["author"], "work": w["work"], "death_ah": w["death_ah"],
                 "function": w["function"], "score": round(s, 2), "loc": page_of(r, q),
                 "verdict_words": cues(raw + " " + nxt, q), "text": excerpt(raw, q, a.context),
                 "then": " ".join(MARK.sub("", nxt).split()[:2 * a.context]) + (" …" if len(nxt.split()) > 2 * a.context else "")})
        out.append(res)

    if a.json:
        json.dump(out, sys.stdout, ensure_ascii=False, indent=1); print(); return
    for res in out:
        print("=" * 100); print("SAYING:", res["saying"])
        print("matched on:", " ".join(res["words_matched_on"]),
              " (too few distinctive words: expect noise; prefer textsearch.py)" if res["too_short_for_loose_match"] else "")
        H = res["hadith"]
        cols = collections.OrderedDict()
        for e in sorted(H, key=lambda e: e["death_ah"] or 9999): cols.setdefault(e["collection"], 0); cols[e["collection"]] += 1
        print(f"\n1. FOUND IN THE COLLECTIONS: {len(H)} hadith in {len(cols)} of {res['collections_searched']} collections"
              + ("" if H else "  -> NOT FOUND in the hadith layer by this wording (a finding: say so)"))
        if cols: print("   " + "; ".join(f"{c} ({n})" for c, n in cols.items()))
        for e in H[:a.limit]:
            num = f"no. {e['number']}" + (" (layer's own count)" if e["numbering"] == "sequential" else "")
            pn = "; ".join(f"{x['edition']}: {x['number']}" for x in e["printed_numbers"])
            print(f"\n   [{e['score']}] {e['collection']} (d. {e['death_ah']} AH), {num}{'; printed ' + pn if pn else ''}")
            print(f"      cite: {e['id']}   narrator: {e['narrator'] or '-'}" + (f"   caliph: {e['caliph']}" if e["caliph"] else ""))
            own = [g for g in e["grades_classical"] if "record" not in g or "Dhahabi" in g["by"]]
            later = [g for g in e["grades_classical"] if g not in own]
            print("      grades in the sources: " + ("; ".join(f"{g['by']}: {g['grade']}" for g in own)
                                                     or "none by the compiler"))
            for g in later:
                amb = f"; {g['candidates']} chains match, read his passage" if g["candidates"] > 1 else ""
                print(f"      {'remark' if g['class'] in ('uniqueness', 'defect_note') else 'critic'}, on the {g['scope']}: {g['by']}: {g['grade'][:220]}  [cite {g['record']} @ {g['loc']}{amb}]")
            for g in e["grades_modern"]:
                print(f"      MODERN (kept apart): {g['by']}: {g['grade'][:160]}  [cite {g['record']}]")
            for cm in e.get("compiler_remark") or []:
                print(f"      the compiler's own remark: {cm[:200]}")
            if e.get("wording_also_in_sahih"):
                comp = {"same": "; from the same Companion", "other": "; from ANOTHER Companion"}.get(e.get("wording_also_in_sahih_companion"), "")
                print(f"      the same wording is also in the Sahih (a note on the wording, not a grade of this chain{comp}): "
                      + ", ".join(e["wording_also_in_sahih"][:4]))
            if e.get("critic_says_in_sahih"):
                print(f"      a classical critic says al-Bukhari or Muslim reported it  [cite {e['critic_says_in_sahih']}]")
            if e.get("parallel_group"):
                print(f"      parallels ({e['parallel_group']}): " + ", ".join(e["parallel_collections"])
                      + ("  [in both al-Bukhari and Muslim, by wording]" if e["agreed_upon_by_wording"] else ""))
            c = e.get("chain")
            if c:
                ln = [f"{n['name']} [{n['grade']}]" for n in c["narrators"] if n.get("grade")]
                print(f"      chain: {c['linked']} of {c['names']} names linked to the Taqrib"
                      + (f"; weakest linked: {c['weakest_linked']}" if c.get("weakest_linked") else "") + " (not a grade of the hadith)")
                if ln: print("         " + " <- ".join(ln[:8]))
            print(f"      {e['text']}")
        if len(H) > a.limit: print(f"\n   ... {len(H) - a.limit} more (raise --limit)")
        if res["entries"]:
            print(f"\n   THE CRITICS' NUMBERED ENTRIES on this saying (apparatus/sayings): {len(res['entries'])}")
            for e in res["entries"][:a.limit]:
                print(f"      {e['critic']} (d. {e['death_ah']} AH), {e['work']} no. {e['entry']} @ {e['loc']}  cues: {e['cues'] or '-'}")
                print(f"         {e['saying'][:120]}")
                if e["verdict"]: print(f"         -> {' '.join(e['verdict'].split()[:a.context + 20])}")
        for key, title in (("collection", "1b. COLLECTIONS NOT YET IN THE HADITH LAYER (searched as text: no grades, parallels or chain data)"),
                           ("critics", "2. THE CLASSICAL CRITICS (oldest first)"), ("modern", "3. MODERN GRADES (kept apart from the classical)"),
                           ("also", "4. ALSO QUOTED IN")):
            L = res[key]
            if key == "also" and not a.also: continue
            if key == "modern" and a.no_modern: continue
            if key == "collection" and not L: continue
            by = collections.OrderedDict()
            for e in L: by.setdefault((e["author"], e["work"], e["death_ah"]), []).append(e)
            print(f"\n{title}: {len(L)} passages in {len(by)} works" + ("" if L else "  -> none found by this wording"))
            shown = 0
            for (au, wk, d), es in by.items():
                print(f"\n   {au} (d. {d} AH), {wk}  [{es[0]['function']}]  {len(es)} passage(s)")
                for e in sorted(es, key=lambda e: -e["score"])[:max(1, a.limit // 2)]:
                    if shown >= a.limit * 3: break
                    shown += 1
                    vw = "; ".join(f"{k}: {'، '.join(v)}" for k, v in e["verdict_words"]) or "none near the quote"
                    print(f"      [{e['score']}] cite: {e['id']}  @ {e['loc']}")
                    print(f"      verdict words nearby: {vw}")
                    print(f"      {e['text']}")
                    if e.get("then"): print(f"      then: {e['then']}")
            if key == "modern" and res.get("entries_modern"):
                print(f"\n   al-Albani's numbered entries (apparatus/sayings/sayings_modern.tsv.gz): {len(res['entries_modern'])}")
                for e in res["entries_modern"][:a.limit]:
                    print(f"      {e['work']} no. {e['entry']}: {e['verdict'][:120]}  [cite {e['record']}]")
                    print(f"         {e['saying'][:120]}")
        print("\nReminder: verdict words are cues, not rulings. Read the passage, cite the record id, keep classical and modern apart.")


if __name__ == "__main__":
    main()
