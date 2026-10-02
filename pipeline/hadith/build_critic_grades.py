#!/usr/bin/env python3
"""
build_critic_grades.py - v44: the later critics' verdicts as data, joined to the hadith layer.

The v35 join of al-Dhahabi's Talkhis showed the method; this script repeats it for the critics whose works state a
verdict in a fixed formula. Every verdict is kept in the critic's own words, with the record to cite. Nothing in the
corpus or the hadith layer is edited: the output is tables.

  misbah    al-Busiri (d. 840), Misbah al-zujaja: each addition of Ibn Maja with "هذا إسناد ..." after it
            -> apparatus/hadith_grades/busiri_misbah_ibnmaja.tsv            joined to Ibn Maja by isnad + matn
  majma     al-Haythami (d. 807), Majma' al-zawa'id: "... رواه أحمد والطبراني ... وفيه فلان وهو ضعيف"
            -> apparatus/hadith_grades/haythami_majma.tsv                   joined by wording to all six of his sources:
                                                                            Ahmad, al-Tabarani's Kabir, and since v46
                                                                            al-Bazzar, Abu Ya'la, the Awsat and Saghir
  albani    al-Albani (d. 1420), Sahih wa-da'if Sunan al-Tirmidhi: "تحقيق الألباني:" after each hadith
            -> apparatus/hadith_grades_modern/albani_tirmidhi.tsv           MODERN: its own folder, never merged
  insahih   for hadith of collections that carry no grade: the same wording is also in al-Bukhari or Muslim
            -> apparatus/hadith_links/in_sahih.tsv.gz                       a note about the WORDING, not a grade

Columns of the grade tables:
  hadith_id      the hadith judged (empty when no hadith in the layer matched: the verdict is kept, unjoined)
  critic, death_ah, layer (classical | modern)
  scope          chain = a verdict on this chain or its narrators ("its narrators are trustworthy" is NOT "the hadith
                 is sound": it says nothing of hidden defects or of the other chains); hadith = a verdict on the hadith
  class          a coarse label derived from his words by rule, for filtering only. Always quote `verdict`, not this.
                 sound | fair | narrators_trustworthy | disputed_narrator | unknown_narrator | weak | very_weak |
                 fabricated | unclassified
  verdict        his words
  match          share of the critic's quoted text found in the joined hadith (0-1)
  candidates     how many hadith in the layer matched equally well. Above 1, the same wording has several chains in
                 the collection and the verdict belongs to ONE of them: read the critic's passage before citing.
  critic_record  the record id to cite; loc = volume:page
  entry          the critic's own entry number where he has one; sources = the collections he names

Joining. Texts are normalised (textnorm.norm), transmission words (حدثنا، ثنا، عن، قال ...) dropped, and compared by
3-word sequences. A verdict joins a hadith when at least half of the critic's quoted sequences occur in it and at least 4 do; when more than
five hadith match equally the wording is too common and the verdict stays unjoined. Quotes under 5 words are not joined.

Usage: python3 pipeline/hadith/build_critic_grades.py [--repo .] [misbah majma albani insahih coverage | all]
Summary: catalogs/critic_grades_summary.json. Everything derived automatically; status unverified until sampled
(see docs/hadith_layer/CRITIC_GRADES.md for the hand-checked sample).
"""
import argparse, collections, csv, gzip, json, os, re, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "search"))
from textnorm import norm  # noqa: E402

WORD = re.compile(r"[ء-ي]{2,}")
MARKS = re.compile(r"Page(?:End)?V\d+P\d+|ms\d+|@Q[BE]@|[#|*~]+")
PAGE = re.compile(r"Page(?:End)?V(\d+)P(\d+)")
TRANS = set(norm(w) for w in """حدثنا ثنا نا أنا أخبرنا أنبأنا أنبأ حدثني أخبرني وحدثنا وحدثني وأخبرنا عن قال قالت قالوا
يقول سمعت سمع أن أنه رسول الله صلى عليه وسلم النبي رضي عنه عنها عنهما تعالى بن ابن أبي أبو""".split())
COLS = ["hadith_id", "critic", "death_ah", "layer", "scope", "class", "verdict", "match", "candidates",
        "critic_record", "loc", "entry", "sources", "quoted"]

CLASS = [  # first match wins, most severe first; applied to the normalised verdict
    ("fabricated", r"موضوع|كذاب|وضاع|يضع الحديث|متهم بالوضع|اتهم بالوضع|باطل|لا اصل له"),
    ("very_weak", r"متروك|كذبه|اتهم|ضعيف جدا|(?<![ء-ي])واه\b|(?<![ء-ي])واهي|منكر الحديث|ساقط|ليس بشيء|مجمع علي ضعفه"),
    ("disputed_narrator", r"وثقه.{0,80}(?:ضعف|وفيه ضعف|خلاف)|ضعفه.{0,80}وثقه|فيه خلاف|مختلف فيه|فيه كلام|وقد وثق|وثق علي ضعف"),
    ("weak", r"مضطرب|يتكلمون فيه|ضعيف|ضعف|ضعفه|لين|مدلس|منقطع|مرسل|معضل|اختلط|سيء الحفظ|فيه مقال|لا يصح|شاذ|منكر|معلول"),
    ("unknown_narrator", r"لم اعرف|لا اعرف|مجهول|لم يسم|لم اجد من (?:ترجم|ذكر)|لم ار من ذكر|من لم اعرف"),
    ("sound", r"اسناد(?:ه|ها|هما)? (?:\S+ )?صحيح|اسانيد\S* صحيح|صحيح الاسناد|رجال(?:ه|ها|هما)? رجال الصحيح|رجال (?:\S+ ){1,4}رجال الصحيح|علي شرط|^صحيح|حسن صحيح"),
    ("fair", r"اسناد(?:ه|ها|هما|ي)? (?:\S+ )?(?:حسن|جيد)|اسانيد\S* (?:حسن|جيد)|^حسن|حسن الحديث|لا باس"),
    ("narrators_trustworthy", r"رجال(?:ه|ها|هما)? (?:ثقات|موثقون)|رجال \S+ (?:ثقات|رجال الصحيح)|ثقات"),
]
CLASS = [(k, re.compile(p.replace(r"\b", r"(?![ء-ي])"))) for k, p in CLASS]


def classify(verdict):
    n = norm(verdict)
    for k, p in CLASS:
        if p.search(n): return k
    return "unclassified"


def clean(t):
    return " ".join(MARKS.sub(" ", t or "").split())


def toks(t):
    return [w for w in WORD.findall(norm(MARKS.sub(" ", t or ""))) if w not in TRANS]


def shingles(ws, k=3):
    return {zlib.crc32(" ".join(ws[i:i + k]).encode()) for i in range(len(ws) - k + 1)}


def J(path):
    with (gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8")) as f:
        for line in f:
            try: yield json.loads(line)
            except ValueError: continue


def raw_of(r):
    t = r.get("text_raw") if isinstance(r.get("text_raw"), str) else r.get("text")
    return t if isinstance(t, str) else ""


class Layer:
    """shingle index over chosen collections of the hadith layer"""
    def __init__(self, repo, collections_, field):
        self.h, self.sh = [], []
        self.idx = collections.defaultdict(list)
        for c in collections_:
            for r in J(os.path.join(repo, f"apparatus/hadith/{c}.jsonl.gz")):
                text = (r.get("isnad") or "") + " " + (r.get("matn") or "") if field == "all" else (r.get("matn") or r.get("isnad") or "")
                s = shingles(toks(text))
                k = len(self.h); self.h.append(r); self.sh.append(s)
                for x in s: self.idx[x].append(k)

    def match(self, text, only=None, thr=0.5, min_hits=4):
        """-> [(share, hadith)] best candidates (all within 10% of the best), or []"""
        s = shingles(toks(text))
        if len(s) < 3: return []
        votes = collections.Counter()
        for x in s:
            L = self.idx.get(x, ())
            if len(L) > 3000: continue
            for k in L: votes[k] += 1
        out = []
        if only: votes = collections.Counter({k: v for k, v in votes.items() if self.h[k]["collection"] in only})
        for k, v in votes.most_common(40):
            share = v / len(s)
            if share >= thr and v >= min(min_hits, len(s)): out.append((share, self.h[k]))
        if not out: return []
        best = max(x[0] for x in out)
        out = [x for x in out if x[0] >= 0.9 * best]
        return out if len(out) <= 5 else []          # wording too common to tell which hadith is meant


def loc_tracker():
    """the true page of a record: OpenITI markers END a page (pipeline/search/pages.py)"""
    def loc(r):
        pb = r.get("page_before")
        return f"{r.get('vol')}:{pb + 1}" if isinstance(pb, int) else ""
    return loc


def write(repo, rel, rows):
    path = os.path.join(repo, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n"); c.writerow(COLS)
        for o in rows: c.writerow([o.get(k, "") for k in COLS])
    joined = [o for o in rows if o["hadith_id"]]
    return {"file": rel, "verdicts": len({(o["critic_record"], o["entry"]) for o in rows}), "rows": len(rows),
            "rows_joined": len(joined), "hadith_with_verdict": len({o["hadith_id"] for o in joined}),
            "hadith_single_candidate": len({o["hadith_id"] for o in joined if o["candidates"] == 1}),
            "class": dict(collections.Counter(o["class"] for o in joined).most_common())}


# ---------- al-Busiri, Misbah al-zujaja -> Ibn Maja ----------
def misbah(repo):
    L = Layer(repo, ["0273IbnMaja.Sunan"], "all"); loc = loc_tracker()
    recs = [r for r in J(os.path.join(repo, "corpus/grading/0840ShihabDinBusiri.MisbahZujaja.jsonl.gz")) if r.get("kind") != "heading"]
    texts = [clean(raw_of(r)) for r in recs]
    NUM = re.compile(r"^\s*\(\s*(\d+)\s*\)\s*")
    VERD = re.compile(r"^(?:قلت\s+)?(?:و)?(?:هذا|هذه)\s+(?:ال)?[إا]سناد|^(?:و)?[إا]سناده\s|^(?:و)?[إا]سناد حديث")
    rows = []
    for i, t in enumerate(texts):
        m = NUM.match(t); v = t[m.end():] if m else t
        if not VERD.search(v): continue
        no = m.group(1) if m else ""
        # the hadith is the run of records before the verdict, back to the separator (the edition puts the
        # entry number either before the hadith or before the verdict)
        body, j = [], i - 1
        while j >= 0 and i - j <= 14:
            u = texts[j]; mu = NUM.match(u); core = u[mu.end():] if mu else u
            if not core or VERD.search(core) or re.match(r"^[-\d\s]*$|^-?\s*\d*\s*باب\s", core): break
            body.append(core)
            if mu: no = no or mu.group(1); break
            j -= 1
        body = " ".join(reversed(body))
        cands = L.match(body, thr=0.5) if body else []
        base = {"critic": "al-Busiri (Misbah al-zujaja)", "death_ah": 840, "layer": "classical", "scope": "chain",
                "class": classify(v), "verdict": v[:600], "critic_record": recs[i]["id"], "loc": loc(recs[i]),
                "entry": no or f"r{i}", "sources": "Ibn Maja", "quoted": body[:160]}
        if not cands: rows.append({**base, "hadith_id": "", "match": "", "candidates": 0})
        for share, h in cands:
            rows.append({**base, "hadith_id": h["id"], "match": round(share, 2), "candidates": len(cands)})
    return write(repo, "apparatus/hadith_grades/busiri_misbah_ibnmaja.tsv", rows)


# ---------- al-Haythami, Majma' al-zawa'id -> Ahmad, al-Tabarani (Kabir) ----------
MAJMA_SOURCES = {"احمد": "0241IbnHanbal.Musnad", "الكبير": "0360Tabarani.MucjamKabir", "الاوسط": "0360Tabarani.MucjamAwsat",
                 "الصغير": "0360Tabarani.MucjamSaghir", "البزار": "0292AbuBakrBazzar.BahrZakhkhar", "ابو يعلي": "0307AbuYaclaMawsili.Musnad"}
NEXT = re.compile(r"\s(?=وعن(?:ه|ها|هم|هما)?\s)")
SRC_END = re.compile(r"\s(?:وفيه|وفيها|وفي |ورجال|ورجاله|واسناد|وإسناد|باسناد|بإسناد|وهو |وله |وقد |ولم |الا ان|إلا أن|وقال|قلت|وروي|ورواه)")
VERDICT_HINT = re.compile(r"رجال|اسناد|ثقات|ضعيف|ضعف|متروك|كذاب|لم اعرف|مجهول|وثق|حسن|صحيح|لين|مدلس|اختلط|لم يسم|منكر|وضاع")


NAME_STOP = set("بن ابن ابي ابو ابا ام عبد الله عبدالله رضي عنه عنها عنهما رسول النبي صلي عليه وسلم مولي بنت".split())
RELATIVE = set("ابيه جده امه عمه رجل ابيها جدته عمته اخيه".split())
SPECIFIC = re.compile(r"(?:رجال|رجاله|اسناد|اسنادي|اسانيد|سند) (احمد|الطبراني|البزار|ابي يعلي|الكبير|الاوسط|الصغير)")


def name_tokens(name):
    return {w for w in WORD.findall(norm(name or "")) if w not in NAME_STOP and len(w) >= 3}


def quoted_narrator(quote, previous):
    """the Companion al-Haythami names at the head of the quote ('عن فلان قال ...'; 'وعنه' = the one before)"""
    n = norm(quote)
    if re.match(r"^و?عن(?:ه|ها|هم|هما)\s", n): return previous
    m = re.match(r"^و?عن\s+(.{3,60}?)\s+(?:قال|قالت|ان|انه|انها|انهم|عن|رفعه|يرفعه|يبلغ|سمعت|كان|كنا)\s", n)
    return name_tokens(m.group(1)) if m else set()


def same_narrator(quoted, h):
    """True / False / None. Does the Companion (or the one reporting from him) that the critic names appear in this
    hadith's chain? The layer's own `narrator` field is a heuristic, so the whole isnad is searched."""
    if not quoted: return None
    t = name_tokens((h.get("narrator") or "") + " " + (h.get("isnad") or ""))
    if not t: return None
    return bool(quoted & t)


def majma_items(text):
    """a paragraph of the Majma' -> [(quoted hadith, 'رواه ...' clause)]"""
    out, start = [], 0
    while True:
        p = text.find("رواه", start)
        if p < 0: break
        m = NEXT.search(text, p)
        q = m.start() if m else len(text)
        out.append((text[start:p].strip(), text[p:q].strip()))
        start = q
        if not m: break
    return out


def majma(repo):
    cols = [c for c in MAJMA_SOURCES.values() if os.path.exists(os.path.join(repo, f"apparatus/hadith/{c}.jsonl.gz"))]
    L = Layer(repo, sorted(set(cols)), "all"); loc = loc_tracker(); cols = set(cols)
    rows = []; n_items = 0; prev_narr = set(); dropped = collections.Counter()
    for r in J(os.path.join(repo, "corpus/grading/0807NurDinHaythami.MajmacZawaid.jsonl.gz")):
        raw = raw_of(r)
        if "رواه" not in raw: continue
        # the true page of each item: markers end a page
        pages, pos = [], 0
        pb = r.get("page_before"); vol, page = r.get("vol"), (pb + 1 if isinstance(pb, int) else None)
        text = ""
        for m in PAGE.finditer(raw):
            seg = clean(raw[pos:m.start()]); pages.append((len(text), vol, page)); text += seg + " "
            vol, page, pos = int(m.group(1)), int(m.group(2)) + 1, m.end()
        pages.append((len(text), vol, page)); text += clean(raw[pos:])
        for quote, tail in majma_items(text):
            n_items += 1
            narr = quoted_narrator(quote, prev_narr); prev_narr = narr or prev_narr
            ntail = norm(tail)
            e = SRC_END.search(ntail)
            src = ntail[:e.start()] if e else ntail
            targets, names = set(), []
            if re.search(r"رواه(?: كله)? (?:الامام )?احمد|واحمد", src): targets.add(MAJMA_SOURCES["احمد"]); names.append("Ahmad")
            if "الطبراني" in src and ("الكبير" in src or not re.search(r"الاوسط|الصغير|الثلاثه", src)):
                targets.add(MAJMA_SOURCES["الكبير"]); names.append("al-Tabarani (Kabir)")
            if "الطبراني" in src and "الثلاثه" in src:
                targets |= {MAJMA_SOURCES["الكبير"], MAJMA_SOURCES["الاوسط"], MAJMA_SOURCES["الصغير"]}; names.append("al-Tabarani (all three)")
            for nm, pat in (("al-Tabarani (Awsat)", "الاوسط"), ("al-Tabarani (Saghir)", "الصغير"), ("al-Bazzar", "البزار"), ("Abu Yaʿla", "ابو يعلي")):
                if pat in src: names.append(nm); targets.add(MAJMA_SOURCES[pat])
            targets &= cols
            if not VERDICT_HINT.search(ntail): continue          # sourcing only ("رواه أحمد"), no verdict stated
            at = text.find(tail[:30]); pg = [x for x in pages if x[0] <= max(at, 0)][-1]
            base = {"critic": "al-Haythami (Majmaʿ al-zawaʾid)", "death_ah": 807, "layer": "classical", "scope": "chain",
                    "class": classify(tail), "verdict": tail[:600], "critic_record": r["id"],
                    "loc": f"{pg[1]}:{pg[2]}" if pg[2] is not None else "", "entry": zlib.crc32(tail.encode()) % 100000,
                    "sources": ", ".join(names), "quoted": quote[:160]}
            # a verdict that names whose narrators it means ("ورجال أحمد ثقات") joins only that collection
            named = set(SPECIFIC.findall(ntail))
            if named:
                keep = {MAJMA_SOURCES[x] for x in named if x in MAJMA_SOURCES}
                if "ابي يعلي" in named: keep.add(MAJMA_SOURCES["ابو يعلي"])
                if "الطبراني" in named: keep |= {MAJMA_SOURCES["الكبير"], MAJMA_SOURCES["الاوسط"], MAJMA_SOURCES["الصغير"]}
                if targets - keep: dropped["verdict_names_another_source"] += 1
                targets &= keep
            cands = L.match(quote, only=targets) if targets else []
            # a chain verdict belongs to the chain of the Companion he names: drop hadith narrated by someone else
            # the wording itself must be shared, not only names in the chain
            qs = shingles(toks(quote))
            cands = [c for c in cands if not c[1].get("matn") or len(qs & shingles(toks(c[1]["matn"]))) >= 3]
            kept = [c for c in cands if same_narrator(narr, c[1]) is not False]
            if cands and not kept: dropped["other_companion"] += 1
            cands = kept
            if not cands: rows.append({**base, "hadith_id": "", "match": "", "candidates": 0}); continue
            for share, h in cands:
                rows.append({**base, "hadith_id": h["id"], "match": round(share, 2), "candidates": len(cands)})
    s = write(repo, "apparatus/hadith_grades/haythami_majma.tsv", rows); s["items_with_rawahu"] = n_items
    s["not_joined_because"] = dict(dropped)
    return s


# ---------- al-Albani on al-Tirmidhi (modern) ----------
def albani(repo):
    L = Layer(repo, ["0279Tirmidhi.Sunan"], "all"); loc = loc_tracker()
    by_no = {}
    for h in L.h:
        for e in h.get("edition_numbers") or []: by_no.setdefault(str(e["number"]), []).append(h)
    recs = [r for r in J(os.path.join(repo, "corpus/modern/1420MuhammadNasirDinAlbani.SahihWaDacifSunanTirmidhi.jsonl.gz")) if r.get("kind") != "heading"]
    rows = []; cur = None
    for i, r in enumerate(recs):
        t = clean(raw_of(r))
        m = re.match(r"^(\d+)\s+(\S.*)", t, re.S)
        if m and i and "سنن الترمذي" in raw_of(recs[i - 1]): cur = (m.group(1), m.group(2)); continue
        if "تحقيق الألباني" in t and cur and i + 1 < len(recs):
            v = clean(raw_of(recs[i + 1])); no, body = cur; cur = None
            if not v or len(v) > 400: continue
            base = {"critic": "al-Albani (Sahih wa-daʿif Sunan al-Tirmidhi)", "death_ah": 1420, "layer": "modern",
                    "scope": "hadith", "class": classify(v), "verdict": v, "critic_record": recs[i + 1]["id"],
                    "loc": loc(recs[i + 1]), "entry": no, "sources": "al-Tirmidhi", "quoted": body[:160]}
            cands = L.match(body, thr=0.5)
            printed = {h["id"] for h in by_no.get(no, [])}
            agree = [c for c in cands if c[1]["id"] in printed]
            if agree: cands = agree
            if not cands: rows.append({**base, "hadith_id": "", "match": "", "candidates": 0}); continue
            for share, h in cands:
                rows.append({**base, "hadith_id": h["id"], "match": round(share, 2), "candidates": len(cands)})
    s = write(repo, "apparatus/hadith_grades_modern/albani_tirmidhi.tsv", rows)
    return s


# ---------- the same wording is also in al-Bukhari / Muslim ----------
def insahih(repo):
    SAHIH = {"0256Bukhari.Sahih", "0261Muslim.Sahih"}
    groups = collections.defaultdict(list)
    with gzip.open(os.path.join(repo, "apparatus/hadith_links/parallels.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"): groups[r["group"]].append(r["hadith_id"])
    want = {h for g in groups.values() if any(x.split(":")[2] in SAHIH for x in g) for h in g}
    sh = {}
    for p in sorted(os.listdir(os.path.join(repo, "apparatus/hadith"))):
        for r in J(os.path.join(repo, "apparatus/hadith", p)):
            if r["id"] in want: sh[r["id"]] = shingles(toks(r.get("matn") or ""))
    path = os.path.join(repo, "apparatus/hadith_links/in_sahih.tsv.gz"); n = 0; per = collections.Counter()
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("hadith_id\tbukhari\tmuslim\toverlap\tparallel_group\n")
        for g, ids in sorted(groups.items()):
            sah = [x for x in ids if x.split(":")[2] in SAHIH]
            if not sah: continue
            for h in ids:
                if h.split(":")[2] in SAHIH or len(sh.get(h, ())) < 3: continue
                best = {}
                for s in sah:
                    if not sh.get(s): continue
                    o = len(sh[h] & sh[s]) / min(len(sh[h]), len(sh[s]))      # the shorter wording inside the longer
                    if o >= 0.6: best[s] = o
                if not best: continue
                b = [x for x in best if "Bukhari" in x]; mu = [x for x in best if "Muslim" in x]
                f.write(f"{h}\t{';'.join(b[:3])}\t{';'.join(mu[:3])}\t{round(max(best.values()), 2)}\t{g}\n")
                n += 1; per[h.split(":")[2]] += 1
    return {"file": "apparatus/hadith_links/in_sahih.tsv.gz", "hadith_with_wording_in_sahih": n, "by_collection": dict(per)}


def coverage(repo):
    """how many hadith of the layer carry a classical grade (the compiler's own, or a critic's verdict joined here)"""
    own, coll = set(), {}
    for p in sorted(os.listdir(os.path.join(repo, "apparatus/hadith"))):
        for r in J(os.path.join(repo, "apparatus/hadith", p)):
            coll[r["id"]] = r["collection"]
            if r.get("grades"): own.add(r["id"])
    crit = set()
    gd = os.path.join(repo, "apparatus/hadith_grades")
    for p in sorted(os.listdir(gd)):
        for r in csv.DictReader(open(os.path.join(gd, p), encoding="utf-8"), delimiter="\t"):
            if r.get("hadith_id"): crit.add(r["hadith_id"])
    sah = set()
    sp = os.path.join(repo, "apparatus/hadith_links/in_sahih.tsv.gz")
    if os.path.exists(sp):
        with gzip.open(sp, "rt", encoding="utf-8") as f: sah = {r["hadith_id"] for r in csv.DictReader(f, delimiter="\t")}
    per = collections.defaultdict(lambda: collections.Counter())
    for h, c in coll.items():
        per[c]["hadith"] += 1; per[c]["compiler_grade"] += h in own; per[c]["critic_verdict"] += h in crit
        per[c]["no_classical_grade"] += h not in own and h not in crit
        per[c]["nothing_at_all"] += h not in own and h not in crit and h not in sah
    tot = collections.Counter()
    for v in per.values(): tot.update(v)
    return {"collections": len(per), **dict(tot), "by_collection": {k: dict(v) for k, v in sorted(per.items())},
            "note": "classical grade = the compiler's own, or a later critic's verdict joined as data. The Sahih wording note is not a grade."}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", nargs="*", default=["all"]); ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    jobs = {"misbah": misbah, "majma": majma, "albani": albani, "insahih": insahih, "coverage": coverage}
    todo = list(jobs) if "all" in a.what else a.what
    sp = os.path.join(a.repo, "catalogs/critic_grades_summary.json")
    summary = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    summary["note"] = "derived automatically; a verdict on a chain is not a grade of the hadith; see docs/hadith_layer/CRITIC_GRADES.md"
    for k in todo:
        summary[k] = jobs[k](a.repo); print(k, json.dumps(summary[k], ensure_ascii=False)[:1500])
    json.dump(summary, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
