#!/usr/bin/env python3
"""
build_grades_v47.py - v47, corrected in v48 (docs/hadith_layer/V48_FIXES.md): five steps to narrow the grade gap of the hadith layer. Tables only; nothing in the
corpus or in apparatus/hadith is edited. Every row is the critic's own words with the record to cite.

1. critics    more classical critics joined to the hadith they judge  -> apparatus/hadith_grades/
     mundhiri_mukhtasar_abidawud.tsv  al-Mundhiri (d. 656), his note after each hadith of Abu Dawud
     nawawi_khulasa.tsv               al-Nawawi (d. 676), Khulasat al-ahkam: "رواه أبو داود بإسناد حسن"; a hadith he
                                      files under "فصل في ضعيفه" is weak by his arrangement (class weak_by_section)
     mundhiri_targhib.tsv             al-Mundhiri, al-Targhib: "رواه أحمد بإسناد جيد"; a hadith he opens with "روي"
                                      is weak by the convention he states in his preface (class weak_by_convention)
     ibnhajar_bulugh.tsv              Ibn Hajar (d. 852), Bulugh al-maram: "رواه أبو داود وصححه ابن خزيمة"
     busiri_ithaf.tsv                 al-Busiri (d. 840), Ithaf al-khayra: "هذا إسناد ضعيف لضعف فلان" on the musnads
2. remarks    the compilers' own remarks on their hadith, as data     -> apparatus/hadith_grades/compilers_remarks.tsv
3. insahih    the Sahih wording note, wider: every hadith is compared with al-Bukhari and Muslim directly (not only
              inside its parallel group), with a check that the Companion is the same, and al-Mundhiri's statements
              "أخرجه البخاري ومسلم" are added                        -> apparatus/hadith_links/in_sahih.tsv.gz
4. narrators  (in build_hadith_links.py) a name that fits several Taqrib entries is settled by its neighbours in
              the chain. Here: the weak narrators Ibn Hajar names in the chains of hadith that have no grade
                                                                      -> apparatus/hadith_links/weak_links.tsv.gz
5. modern     a modern column, apart                                 -> apparatus/hadith_grades_modern/
     albani_abidawud.tsv        al-Albani on Abu Dawud, as the editor printed it in al-Mundhiri's Mukhtasar
     arnaut_ahmad.tsv           Shu'ayb al-Arna'ut on Ahmad's Musnad (the Qurtuba printing that carries his notes)
     husayn_asad_darimi.tsv     Husayn Salim Asad on al-Darimi
     husayn_asad_abuyacla.tsv   Husayn Salim Asad on Abu Ya'la
     albani_jami.tsv            al-Albani on al-Suyuti's Jami' saghir, joined by wording to every collection
   The three editions are fetched from OpenITI at pinned commits (catalogs/modern_editions_pins.json) into
   sources/openiti/modern_editions/. They are not corpus works and are not searched: only the verdicts are taken.

Columns are those of build_critic_grades.py. New classes: disputed (the critic reports both a strengthening and a
weakening verdict), in_sahihayn (he says al-Bukhari or Muslim reported it), weak_by_section, weak_by_convention,
sound_by_support (sound or fair through other routes while this chain is weak: "صحيح لغيره", "صحيح وهذا إسناد ضعيف"),
uniqueness and defect_note (remarks that are not grades and are not counted as grades).
When a verdict names several collections it is joined to each one held; the chain he means may be one of them.

Usage: python3 pipeline/hadith/build_grades_v47.py [--repo .] [--fetch] [step ... | all]
Summary: catalogs/critic_grades_summary.json (keys v47_*, coverage). Derived automatically; unverified until sampled.
"""
import argparse, collections, csv, gzip, hashlib, io, json, os, re, sys, urllib.request, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "search"))
import build_critic_grades as B  # noqa: E402
from textnorm import norm  # noqa: E402

J, clean, raw_of, toks, shingles, COLS = B.J, B.clean, B.raw_of, B.toks, B.shingles, B.COLS
A = "(?<![ء-ي])"; Z = "(?![ء-ي])"

# ---------- classes: stricter than v44 (whole words), with reported verdicts ----------
NEG = [("fabricated", rf"{A}(?:موضوع|كذاب|وضاع|يضع الحديث|باطل|لا اصل له){Z}"),
       ("very_weak", rf"{A}(?:متروك|ضعيف جدا|واه|واهي|منكر الحديث|ساقط|ليس بشيء|مجمع علي ضعفه){Z}"),
       ("weak", rf"{A}و?(?:ب?سند ضعيف|مضطرب|ضعيف|ضعفه|ضعف|فيه ضعف|لين|فيه لين|مدلس|منقطع|مرسل|معضل|اختلط|سيء الحفظ|فيه مقال|"
                rf"لا يصح|لا يثبت|شاذ|منكر|معلول|اعله|اعل|ليس بالقوي|ليس بقوي|لا يحتج به|لم يسمع|فيه نظر|غير محفوظ|ضعفوه|ضعفوا|مقال|نكاره|مناكير){Z}"),
       ("unknown_narrator", rf"{A}(?:لم اعرفه|لا اعرفه|مجهول|لم يسم|لا يعرف|جهاله){Z}")]
POS = [("sound", rf"اسناد\S* (?:\S+ )?صحيح|اسانيد\S* صحيح|سند\S* صحيح|صحيح الاسناد|رجال\S* رجال الصحيح|علي شرط|{A}و?صححه{Z}|"
                 rf"{A}حديث (?:حسن )?صحيح|^\W*صحيح|حسن صحيح|اسناد\S* قوي|{A}و?هو صحيح"),
       ("fair", rf"اسناد\S* (?:\S+ )?(?:حسن|جيد)|اسانيد\S* (?:حسن|جيد)|سند\S* (?:حسن|جيد)|^\W*حسن{Z}|(?<!بن ){A}و?حسنه{Z}|"
                rf"{A}حديث حسن|لا باس ب|{A}و?هو حسن"),
       ("narrators_trustworthy", rf"{A}(?:رجال\S*|رواته|رواتهم|كلهم) (?:\S+ )?(?:ثقات|موثقون|محتج بهم)")]
NEG = [(k, re.compile(p)) for k, p in NEG]; POS = [(k, re.compile(p)) for k, p in POS]
DISPUTED_N = re.compile(r"وثقه.{0,80}(?:ضعف|خلاف)|ضعفه.{0,80}وثقه|فيه خلاف|مختلف فيه|مختلف في (?:توثيقه|الاحتجاج به|عدالته|حاله)|فيه كلام|وقد وثق|اختلف فيه|اختلفوا في")
# v48: a reservation after a strengthening verdict ("إسناده صحيح لكن قوى أبو حاتم إرساله", "كلهم ثقات والصواب موقوف")
RESERVE = re.compile(rf"{A}(?:ارساله|وقفه|انقطاعه){Z}|الصواب (?:\S+ )?(?:موقوف|مرسل|وقفه|ارساله)|(?:الموقوف|المرسل|وقفه|ارساله) (?:هو )?(?:اصح|الصواب|اشبه)")
# v48: "رواه فلان بإسناد حسن" states the grade of the chain in hand; later words may report other routes
CHAIN_GRADE = re.compile(r"ب(?:اسناد|سند|اسانيد) (?:\S+ )?(صحيح|صحيحه|قوي|حسن|حسنه|جيد|جيده|ضعيف|ضعيفه)")
SUPPORT = re.compile(r"(?:صحيح|حسن) لغيره|^\W*(?:حديث )?(?:صحيح|حسن)(?: صحيح)?[\s،,]+(?:و)?(?:هذا )?اسناد\S* (?:\S+ )?ضعيف|بشواهده|بطرقه|بمجموع طرقه|اسناد\S* ضعيف.{0,40}(?:الحديث|المتن|متنه) صحيح|(?:غير ان|لكن) الحديث صحيح")
GRADE_CLASSES = {"sound_by_support", "sound", "fair", "narrators_trustworthy", "disputed", "disputed_narrator", "unknown_narrator", "weak",
                 "very_weak", "fabricated", "weak_by_section", "weak_by_convention"}


def classify(v):
    n = norm(v)
    neg = next((k for k, p in NEG if p.search(n)), None)
    pos = next((k for k, p in POS if p.search(n)), None)
    cg = CHAIN_GRADE.search(n)
    if cg and pos and cg.group(1).startswith(("حسن", "جيد")): pos = "fair"
    if pos and not neg and RESERVE.search(n): neg = "weak"
    if SUPPORT.search(n): return "sound_by_support"
    if DISPUTED_N.search(n): return "disputed_narrator"
    if neg and pos: return "disputed"
    return neg or pos or "unclassified"


SCOPE_HADITH = re.compile(rf"قال (?:\S+ ){{1,2}}?(?:هذا )?(?:حديث )?(?:حسن|صحيح|غريب){Z}|{A}حديث (?:حسن|صحيح|ضعيف|منكر|غريب)|^\W*(?:حسن|صحيح|ضعيف){Z}|{A}و?(?:صححه|حسنه|ضعفه){Z}|{A}وهو (?:حسن|صحيح|ضعيف)")


SRC_STOP = re.compile(r"وصحح|وحسن|وضعف|وقال|باسناد|بسند|باسانيد|وفي |وفيه|ورجال|وروات|واسناد|علي شرط|ولكن|الا ان")


def sahih_source(tail):
    """the critic names al-Bukhari or Muslim among those who REPORTED it (not 'on Muslim's conditions', not 'al-Bukhari graded it')"""
    n = norm(tail); m = SRC_STOP.search(n)
    return bool(SAHIHAYN_SRC.search(n[:m.start()] if m else n))


def scope_of(v):
    return "hadith" if SCOPE_HADITH.search(norm(v)) else "chain"


# ---------- the collections a critic names ----------
C = {"AD": "0275AbuDawudSijistani.Sunan", "T": "0279Tirmidhi.Sunan", "N": "0303Nasai.SunanSughra", "NK": "0303Nasai.SunanKubra",
     "IM": "0273IbnMaja.Sunan", "A": "0241IbnHanbal.Musnad", "DM": "0255CabdAllahDarimi.Sunan", "DQ": "0385Daraqutni.Sunan",
     "H": "0405HakimNaysaburi.Mustadrak", "IK": "0311IbnKhuzaymaNaysaburi.Sahih", "IH": "0739CalaDinIbnBalban.Ihsan",
     "TK": "0360Tabarani.MucjamKabir", "TA": "0360Tabarani.MucjamAwsat", "TS": "0360Tabarani.MucjamSaghir",
     "BZ": "0292AbuBakrBazzar.BahrZakhkhar", "AY": "0307AbuYaclaMawsili.Musnad", "SH": "0458Bayhaqi.ShucabIman",
     "HM": "0219IbnZubayrHumaydi.Musnad", "TY": "0204AbuDawudTayalisi.Musnad"}
NAMES = [("Abu Dawud al-Tayalisi", rf"ابو داود الطيالسي|{A}الطيالسي", ["TY"]), ("Abu Dawud", rf"ابو داود(?! الطيالسي)|{A}وابي داود|سنن ابي داود", ["AD"]),
         ("al-Tirmidhi", rf"{A}و?الترمذي", ["T"]), ("al-Nasaʾi", rf"{A}و?النسايي", ["N", "NK"]), ("Ibn Maja", r"ابن ماجه", ["IM"]),
         ("Ahmad", rf"{A}و?احمد(?! بن منيع)", ["A"]), ("al-Darimi", rf"{A}و?الدارمي", ["DM"]), ("al-Daraqutni", rf"{A}و?الدارقطني", ["DQ"]),
         ("al-Hakim", rf"{A}و?الحاكم", ["H"]), ("Ibn Khuzayma", r"ابن خزيمه", ["IK"]), ("Ibn Hibban", r"ابن حبان", ["IH"]),
         ("al-Bazzar", rf"{A}و?البزار", ["BZ"]), ("Abu Yaʿla", r"ابو يعلي|ابي يعلي", ["AY"]), ("al-Humaydi", rf"{A}و?الحميدي", ["HM"]),
         ("al-Bayhaqi (Shuʿab)", r"البيهقي في (?:ال)?شعب|شعب الايمان", ["SH"]),
         ("the Four", rf"{A}و?الاربعه|اصحاب السنن", ["AD", "T", "N", "NK", "IM"]), ("the Three", rf"{A}و?الثلاثه", ["AD", "T", "N", "NK"]),
         ("the Five", rf"{A}و?الخمسه", ["A", "AD", "T", "N", "NK", "IM"]), ("the Six", rf"{A}و?(?:السته|الجماعه)", ["AD", "T", "N", "NK", "IM"]),
         ("the Seven", rf"{A}و?السبعه", ["A", "AD", "T", "N", "NK", "IM"])]
NAMES = [(n, re.compile(p), [C[x] for x in cs]) for n, p, cs in NAMES]
SAHIHAYN = re.compile(rf"متفق عليه|{A}و?(?:ال)?بخاري|{A}و?(?:ل)?مسلم{Z}|الشيخان|اخرجاه|الصحيحين")
SAHIHAYN_SRC = re.compile(rf"متفق عليه|{A}و?البخاري{Z}|{A}و?مسلم{Z}|الشيخان|اخرجاه")
CHAIN_CUE = re.compile(r"باسناد|بسند|باسانيد")
HINT = re.compile(rf"رجال|رواته|اسناد|اسانيد|بسند|ثقات|ضعيف|ضعف|متروك|كذاب|مجهول|وثق|حسن|صحيح|صحح|{A}لين{Z}|مدلس|اختلط|لم يسم|منكر|"
                  rf"وضاع|موضوع|جيد|قوي|مرسل|منقطع|مضطرب|معلول|{A}اعل|لا باس|مقال|{A}واه|لا يثبت|لا يصح")


def named(tail):
    """-> (names, collections) the critic names; when he says 'رواه X بإسناد ...' only those before the cue"""
    n = norm(tail)
    def scan(s):
        names, cols = [], []
        for nm, p, cs in NAMES:
            if p.search(s):
                names.append(nm); cols += cs
        if "الطبراني" in s:
            k = [x for x, w in (("TK", "الكبير"), ("TA", "الاوسط"), ("TS", "الصغير")) if w in s] or ["TK"]
            if "الثلاثه" in s: k = ["TK", "TA", "TS"]
            names.append("al-Tabarani (" + "/".join(k) + ")"); cols += [C[x] for x in k]
        return names, cols
    m = CHAIN_CUE.search(n)
    if m:
        names, cols = scan(n[:m.start()])
        if cols: return names, list(dict.fromkeys(cols))
    names, cols = scan(n)
    return names, list(dict.fromkeys(cols))


class Layer(B.Layer):
    by_no = None

    def numbers(self):
        if self.by_no is None:
            self.by_no = collections.defaultdict(list)
            for h in self.h: self.by_no[(h["collection"], str(h["number"]))].append(h)
        return self.by_no


def join(L, quote, targets, narr=None, need_matn=True):
    cands = L.match(quote, only=set(targets)) if targets else []
    if need_matn:
        qs = shingles(toks(quote))
        cands = [c for c in cands if not c[1].get("matn") or len(qs & shingles(toks(c[1]["matn"]))) >= 3]
    if narr:
        kept = [c for c in cands if B.same_narrator(narr, c[1]) is not False]
        cands = kept
    return cands


def emit(rows, base, cands):
    if not cands: rows.append({**base, "hadith_id": "", "match": "", "candidates": 0}); return
    for share, h in cands: rows.append({**base, "hadith_id": h["id"], "match": round(share, 2), "candidates": len(cands)})


def write(repo, rel, rows):
    seen, uniq = set(), []                      # v48: the same verdict on the same hadith is written once
    for o in rows:
        k = (o["hadith_id"], o["critic_record"], str(o["entry"]), o["verdict"]) if o["hadith_id"] else id(o)
        if k in seen: continue
        seen.add(k); uniq.append(o)
    rows[:] = uniq
    s = B.write(repo, rel, rows)
    s["rows_joined_with_a_grade"] = sum(1 for o in rows if o["hadith_id"] and o["class"] in GRADE_CLASSES)
    s["hadith_with_a_grade"] = len({o["hadith_id"] for o in rows if o["hadith_id"] and o["class"] in GRADE_CLASSES})
    return s


def all_cols(repo):
    return sorted(p[:-9] for p in os.listdir(os.path.join(repo, "apparatus/hadith")) if p.endswith(".jsonl.gz"))


_L = {}
def layer(repo):
    if "all" not in _L: _L["all"] = Layer(repo, all_cols(repo), "all")
    return _L["all"]


def page_loc(r):
    pb = r.get("page_before")
    return f"{r.get('vol')}:{pb + 1}" if isinstance(pb, int) else ""


TAIL_CUE = re.compile(r"(?:^|[\s.»\"'،,:])(و?رواه|و?اخرجه|متفق عليه|اخرجاه|و?رويناه|(?:حديث )?(?:حسن|صحيح|ضعيف) ?[،,] ?رواه)")
QEND = re.compile(r"[»'\"](?!.*[»'\"])", re.S)


def split_tail(t):
    """a hadith followed by 'رواه ...': -> (quote, tail). The tail starts at the first cue after the last closing quote."""
    q = QEND.search(t); start = q.end() if q else 0
    n = t  # cues are searched on the raw text with light normalising of alif
    m = re.search(r"(?:^|[\s.»\"'،,:])((?:حسن|صحيح|ضعيف)\s*[،,]\s*رواه|و?رواه|و?[أا]خرجه|متفق عليه|[أا]خرجاه|و?رويناه)", n[start:])
    if not m and start:
        start = 0; m = re.search(r"(?:^|[\s.»\"'،,:])(و?رواه|و?[أا]خرجه|متفق عليه|[أا]خرجاه)", n)
    if not m: return t, ""
    return t[:start + m.start(1)].strip(), t[start + m.start(1):].strip()


# ---------- 1a. al-Mundhiri, Mukhtasar Sunan Abi Dawud (+ 5a. al-Albani's tags printed in it) ----------
def mundhiri_mukhtasar(repo):
    L = layer(repo); AD = C["AD"]; by_no = L.numbers()
    recs = [r for r in J(os.path.join(repo, "corpus/grading/0656IbnCabdQawiMundhiri.MukhtasarSunanAbiDawud.jsonl.gz")) if r.get("kind") != "heading"]
    HEAD = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*-\s*(.*)$", re.S); TAG = re.compile(r"\.?h([^\]\n]{1,60})\]")
    classical, modern = [], []; cur = None
    def target(cur):
        if "cands" not in cur:
            cands = L.match(cur["body"], only={AD}, thr=0.4)
            agree = [c for c in cands if str(c[1]["number"]) == cur["ad_no"]]
            if not agree and by_no.get((AD, cur["ad_no"])):      # the printed number is Abu Dawud's own: trust it when the wording shares anything
                qs = shingles(toks(cur["body"]))
                agree = [(round(len(qs & shingles(toks((h.get("isnad") or "") + " " + (h.get("matn") or "")))) / max(len(qs), 1), 2), h)
                         for h in by_no[(AD, cur["ad_no"])]]
                agree = [c for c in agree if c[0] >= 0.25]
            cur["cands"] = agree or (cands if len(cands) == 1 and cands[0][0] >= 0.7 else [])
        return cur["cands"]
    for r in recs:
        t = clean(raw_of(r)); m = HEAD.match(t)
        if m:
            body = TAG.sub(" ", m.group(3)); cur = {"ad_no": m.group(1), "mk_no": m.group(2), "body": body, "rec": r}
            for tag in TAG.findall(m.group(3)):
                tag = tag.strip()
                base = {"critic": "al-Albani (his verdict as printed by the editor of al-Mundhiri's Mukhtasar)", "death_ah": 1420,
                        "layer": "modern", "scope": "chain" if "الإسناد" in tag else "hadith", "class": classify(tag), "verdict": tag,
                        "critic_record": r["id"], "loc": page_loc(r), "entry": m.group(1), "sources": "Abu Dawud", "quoted": body[:160]}
                emit(modern, base, target(cur))
            continue
        if t.startswith("•") and cur:
            note = TAG.sub(" ", t.lstrip("• ").strip())
            for tag in TAG.findall(t):                      # a tag printed after the note belongs to the same hadith
                base = {"critic": "al-Albani (his verdict as printed by the editor of al-Mundhiri's Mukhtasar)", "death_ah": 1420,
                        "layer": "modern", "scope": "chain" if "الإسناد" in tag else "hadith", "class": classify(tag), "verdict": tag.strip(),
                        "critic_record": r["id"], "loc": page_loc(r), "entry": cur["ad_no"], "sources": "Abu Dawud", "quoted": cur["body"][:160]}
                emit(modern, base, target(cur))
            n = norm(note); cls = classify(note)
            # a quoted report continued after the bullet is not his note
            if not re.match(r"^و?(?:اخرجه|في اسناده|قال|هذا|هكذا|ذكر|حكي|وقد|اسناده|رواه|فيه|في |ابو|هو|وهو|و)", n): continue
            if cls == "unclassified":
                if re.search(r"اخرجه", n) and SAHIHAYN.search(n): cls = "in_sahihayn"
                else: continue                                                   # sourcing only, or an explanation
            base = {"critic": "al-Mundhiri (Mukhtasar Sunan Abi Dawud)", "death_ah": 656, "layer": "classical",
                    "scope": "takhrij" if cls == "in_sahihayn" else scope_of(note),
                    "class": cls, "verdict": note[:600], "critic_record": r["id"], "loc": page_loc(r), "entry": cur["ad_no"],
                    "sources": "Abu Dawud", "quoted": cur["body"][:160]}
            emit(classical, base, target(cur))
    s1 = write(repo, "apparatus/hadith_grades/mundhiri_mukhtasar_abidawud.tsv", classical)
    s2 = write(repo, "apparatus/hadith_grades_modern/albani_abidawud.tsv", modern)
    return {"mundhiri": s1, "albani_abidawud": s2}


# ---------- 1b. al-Nawawi, Khulasat al-ahkam ----------
def khulasa(repo):
    L = layer(repo); rows = []; weak_section = False; prev_narr = set(); st = collections.Counter()
    for r in J(os.path.join(repo, "corpus/grading/0676Nawawi.KhulasatAhkam.jsonl.gz")):
        t = clean(raw_of(r))
        if r.get("kind") == "heading" or re.match(r"^\(?\s*\d*\s*\(\s*(?:باب|فصل|كتاب)", t) or re.match(r"^\d+\s*\(", t):
            if "فصل في ضعيف" in t: weak_section = True
            elif re.search(r"باب|كتاب|فصل", t): weak_section = False
            continue
        m = re.match(r"^(\d+)\s*-\s*(.*)$", t, re.S)
        if not m: continue
        body = re.sub(r"\[\s*\d+\s*/\s*[أب]\s*(?:/\s*)?\]", " ", m.group(2))
        quote, tail = split_tail(body)
        if not tail: continue
        st["items"] += 1
        narr = B.quoted_narrator(quote, prev_narr); prev_narr = narr or prev_narr
        names, cols = named(tail); has = HINT.search(norm(tail))
        if not has and not weak_section: st["sourcing_only"] += 1; continue
        cls = classify(tail)
        if weak_section and cls in ("unclassified", "sound", "fair", "narrators_trustworthy") and not has: cls = "weak_by_section"
        elif weak_section and cls == "unclassified": cls = "weak_by_section"
        if cls == "unclassified": st["unclassified"] += 1; continue
        if cls in ("sound", "fair", "narrators_trustworthy") and sahih_source(tail): cls = "in_sahihayn"
        base = {"critic": "al-Nawawi (Khulasat al-ahkam)", "death_ah": 676, "layer": "classical",
                "scope": "takhrij" if cls == "in_sahihayn" else "hadith" if cls == "weak_by_section" else scope_of(tail), "class": cls,
                "verdict": (("[فصل في ضعيفه] " if weak_section else "") + tail)[:600], "critic_record": r["id"], "loc": page_loc(r),
                "entry": m.group(1), "sources": ", ".join(names), "quoted": quote[:160]}
        emit(rows, base, join(L, quote, cols, narr))
    s = write(repo, "apparatus/hadith_grades/nawawi_khulasa.tsv", rows); s.update(st); return s


# ---------- 1c. Ibn Hajar, Bulugh al-maram ----------
def bulugh(repo):
    L = layer(repo); rows = []; no = ""; prev_narr = set(); st = collections.Counter()
    for r in J(os.path.join(repo, "corpus/grading/0852IbnHajarCasqalani.BulughMaram.jsonl.gz")):
        raw = raw_of(r)
        if r.get("kind") == "heading":
            m = re.search(r"(\d+)\s*-", raw); no = m.group(1) if m else no; continue
        t = re.sub(r"\(\d+\)", " ", clean(raw)); quote, tail = split_tail(t)
        if not tail: continue
        st["items"] += 1
        narr = B.quoted_narrator(quote, prev_narr); prev_narr = narr or prev_narr
        if not HINT.search(norm(tail)): st["sourcing_only"] += 1; continue
        cls = classify(tail)
        if cls == "unclassified": st["unclassified"] += 1; continue
        names, cols = named(tail)
        if cls in ("sound", "fair", "narrators_trustworthy") and sahih_source(tail): cls = "in_sahihayn"
        base = {"critic": "Ibn Hajar (Bulugh al-maram)", "death_ah": 852, "layer": "classical", "scope": "takhrij" if cls == "in_sahihayn" else scope_of(tail), "class": cls,
                "verdict": tail[:600], "critic_record": r["id"], "loc": page_loc(r), "entry": no, "sources": ", ".join(names), "quoted": quote[:160]}
        emit(rows, base, join(L, quote, cols, narr))
    s = write(repo, "apparatus/hadith_grades/ibnhajar_bulugh.tsv", rows); s.update(st); return s


# ---------- 1d. al-Mundhiri, al-Targhib wa-l-tarhib ----------
def targhib(repo):
    L = layer(repo); rows = []; st = collections.Counter(); prev_narr = set()
    recs = [r for r in J(os.path.join(repo, "corpus/grading/0656IbnCabdQawiMundhiri.TarghibWaTarhib.jsonl.gz")) if r.get("kind") != "heading"]
    cur = None
    for r in recs:
        t = clean(raw_of(r))
        m = re.match(r"^(\d+)\s+(\S.*)$", t, re.S)
        if m: cur = {"no": m.group(1), "body": m.group(2)}; continue
        if not t or t == "#": continue
        if cur and re.match(r"^و?رواه\s", t):
            if cur.get("done"): continue                    # a second 'ورواه' paragraph: other wordings
            cur["done"] = True; st["items"] += 1
            quote, tail = cur["body"], t
            narr = B.quoted_narrator(quote, prev_narr); prev_narr = narr or prev_narr
            ruwiya = bool(re.match(r"^و?روي\s", norm(quote)))
            has = HINT.search(norm(tail)); cls = classify(tail)
            if cls == "unclassified" and ruwiya: cls = "weak_by_convention"
            if cls == "unclassified" or (not has and not ruwiya): st["sourcing_only"] += 1; continue
            names, cols = named(tail)
            if cls in ("sound", "fair", "narrators_trustworthy") and sahih_source(tail): cls = "in_sahihayn"
            base = {"critic": "al-Mundhiri (al-Targhib wa-l-tarhib)", "death_ah": 656, "layer": "classical",
                    "scope": "takhrij" if cls == "in_sahihayn" else "hadith" if cls == "weak_by_convention" else scope_of(tail), "class": cls, "verdict": tail[:600],
                    "critic_record": r["id"], "loc": page_loc(r), "entry": cur["no"], "sources": ", ".join(names), "quoted": quote[:160]}
            emit(rows, base, join(L, quote, cols, narr))
        elif cur and not cur.get("done"): cur["body"] += " " + t
    s = write(repo, "apparatus/hadith_grades/mundhiri_targhib.tsv", rows); s.update(st); return s


# ---------- 1e. al-Busiri, Ithaf al-khayra ----------
ITHAF_SRC = [("Abu Yaʿla", r"ابو يعلي", "AY"), ("Ahmad", r"احمد بن حنبل", "A"), ("Abu Dawud al-Tayalisi", r"ابو داود الطيالسي|الطيالسي", "TY"),
             ("al-Humaydi", r"الحميدي", "HM"), ("al-Bazzar", r"البزار", "BZ")]
ITHAF_OTHER = r"مسدد|ابو بكر بن ابي شيبه|احمد بن منيع|الحارث|اسحاق بن راهويه|عبد بن حميد|محمد بن يحيي|ابن ابي عمر"


def ithaf(repo):
    L = layer(repo); rows = []; st = collections.Counter()
    VERD = re.compile(r"^(?:قلت[:،]?\s*)?(?:و)?(?:هذا|هذه)\s+(?:ال)?[إا]سناد|^قلت[:،]|^و?[إا]سناده\s|^و?رواه\s")
    HEADQ = re.compile(r"^و?قال\s+(.{3,45}?)\s*[:،]\s*(?:و)?(?:ثنا|حدثنا|انا|ابنا|اخبرنا|انبانا|نا|حدثني)\s")
    group, comp = [], None; gno = None
    def flush():
        hadith = [x for x in group if x["kind"] == "h"]
        for i, x in enumerate(group):
            if x["kind"] != "v": continue
            prev = [h for h in group[:i] if h["kind"] == "h" and len(toks(h["text"])) >= 8]
            if not prev: continue
            h = prev[-1]; tail = x["text"]; n = norm(tail)
            if not HINT.search(n): continue
            cls = classify(tail)
            if cls == "unclassified": continue
            st["verdicts"] += 1
            srcs = [(nm, C[c]) for nm, p, c in ITHAF_SRC if re.search(p, n)] if re.match(r"^و?رواه", n) else []
            if not srcs and h.get("comp"): srcs = [h["comp"]] if h["comp"][1] else []
            if not srcs and not re.match(r"^و?رواه", n) and not h.get("comp"): st["source_unknown"] += 1
            base = {"critic": "al-Busiri (Ithaf al-khayra)", "death_ah": 840, "layer": "classical", "scope": scope_of(tail) if "حديث" in n[:30] else "chain",
                    "class": cls, "verdict": tail[:600], "critic_record": x["rec"]["id"], "loc": page_loc(x["rec"]), "entry": x["no"],
                    "sources": ", ".join(nm for nm, _ in srcs) or (h.get("comp_name") or ""), "quoted": h["text"][:160]}
            cands = L.match(h["text"], only={c for _, c in srcs}, thr=0.5) if srcs else []
            emit(rows, base, cands)
    for r in J(os.path.join(repo, "corpus/grading/0840ShihabDinBusiri.IthafKhayra.jsonl.gz")):
        raw = raw_of(r)
        if r.get("kind") == "heading":
            m = re.search(r"(\d+)(?:\s*/\s*(\d+))?\s*-", raw)
            if m:
                if m.group(1) != gno: flush(); group = []; comp = None; gno = m.group(1)
                no = m.group(1) + ("/" + m.group(2) if m.group(2) else "")
            elif "باب" in raw or "كتاب" in raw: flush(); group = []; comp = None; gno = None
            continue
        t = clean(raw)
        if not t or gno is None: continue
        n = norm(t)
        if VERD.search(t) or VERD.search(n):
            group.append({"kind": "v", "text": t, "rec": r, "no": no})
        else:
            m = HEADQ.match(n); cname = None
            if m:
                who = m.group(1)
                hit = next(((nm, C[c]) for nm, p, c in ITHAF_SRC if re.search(p, who)), None)
                if hit: comp = hit
                elif re.search(ITHAF_OTHER, who): comp = (who, None)
                elif who.strip() in ("", "و"): pass
                cname = who
            elif re.match(r"^قال\s*[:،]\s*و?(?:ثنا|حدثنا)", n): pass                   # 'قال: وثنا' = the same compiler
            elif re.match(r"^و?عن\s", n): comp = None                                # matn only; the source comes with 'رواه'
            if group and group[-1]["kind"] == "h" and not m and not re.match(r"^(?:قال\s*[:،]|و?عن\s)", n):
                group[-1]["text"] += " " + t                                         # a hadith broken across a page
            else:
                group.append({"kind": "h", "text": t, "comp": comp, "comp_name": comp[0] if comp else cname, "rec": r})
    flush()
    s = write(repo, "apparatus/hadith_grades/busiri_ithaf.tsv", rows); s.update(st); return s


def critics(repo):
    out = mundhiri_mukhtasar(repo)
    out["khulasa"] = khulasa(repo); out["bulugh"] = bulugh(repo); out["targhib"] = targhib(repo); out["ithaf"] = ithaf(repo)
    return out


# ---------- 2. the compilers' own remarks ----------
COMPILER = {"0275AbuDawudSijistani.Sunan": ("Abu Dawud", 275), "0279Tirmidhi.Sunan": ("al-Tirmidhi", 279), "0303Nasai.SunanSughra": ("al-Nasaʾi", 303),
            "0303Nasai.SunanKubra": ("al-Nasaʾi", 303), "0385Daraqutni.Sunan": ("al-Daraqutni", 385), "0458Bayhaqi.ShucabIman": ("al-Bayhaqi", 458),
            "0311IbnKhuzaymaNaysaburi.Sahih": ("Ibn Khuzayma", 311), "0292AbuBakrBazzar.BahrZakhkhar": ("al-Bazzar", 292),
            "0360Tabarani.MucjamAwsat": ("al-Tabarani", 360), "0360Tabarani.MucjamSaghir": ("al-Tabarani", 360), "0360Tabarani.MucjamKabir": ("al-Tabarani", 360),
            "0255CabdAllahDarimi.Sunan": ("al-Darimi", 255), "0241IbnHanbal.Musnad": ("Ahmad / ʿAbd Allah b. Ahmad", 241),
            "0273IbnMaja.Sunan": ("Ibn Maja", 273), "0405HakimNaysaburi.Mustadrak": ("al-Hakim", 405), "0307AbuYaclaMawsili.Musnad": ("Abu Yaʿla", 307),
            "0204AbuDawudTayalisi.Musnad": ("al-Tayalisi", 204), "0219IbnZubayrHumaydi.Musnad": ("al-Humaydi", 219),
            "0739CalaDinIbnBalban.Ihsan": ("Ibn Hibban", 354)}
# remarks that stand unmarked at the end of the text (al-Daraqutni, al-Bayhaqi, Ibn Khuzayma): critic's vocabulary only
TAIL_REMARK = re.compile(
    r"(?:^|\s)((?:و?(?:هذا|هذه)\s+(?:ال)?(?:إسناد|اسناد|مرسل|منقطع|حديث\s+(?:منكر|ضعيف|غريب|باطل|لا يصح|لا يثبت)|خبر\s+(?:منكر|غريب|ليس))"
    r"|و?(?:إ|ا)سناد(?:ه)?\s+(?:صحيح|حسن|ضعيف|ليس)|(?:كلهم|رواته|رجاله)\s+ثقات|تفرد\s+به|و?لا\s+(?:يثبت|يصح)|و?(?:في|وفي)\s+(?:إ|ا)سناده"
    r"|و?(?:ال)?موقوف\s+(?:أصح|اصح|هو الصواب)|و?(?:ال)?مرسل\s+(?:أصح|اصح)|و?(?:ال)?صواب|غير\s+محفوظ|لم\s+يسمع\s+(?:من|هذا)|و?خالفه\s"
    r"|إن\s+صح\s+الخبر|ان\s+صح\s+الخبر|في\s+القلب\s+من|لست\s+أعرف|فإني\s+لا\s+أعرف|أنا\s+أبرأ\s+من\s+عهدة"
    r").*)$", re.S)
# a remark that ends the text with the verdict word after the narrator's name: "... رشدين ضعيف"
NAME_FINAL = re.compile(r"(?:^|\s)((?:وهو\s+|هذا\s+)?(?:ضعيف|متروك|مجهول|ليس\s+بالقوي|ليس\s+بقوي|لا\s+يحتج\s+به|منكر\s+الحديث|مضطرب\s+الحديث|ضعيفان|متروكان)(?:\s+الحديث)?)\s*$")
NAME_PASS = set(norm(w) for w in "بن ابن أبي أبو أبا بنت عبد هو وهو هذا غير عن".split())


def name_final(text, isnad):
    """v48: -> the remark, starting at the narrator's name. The name is taken back from the verdict word for as long as
    its words occur in this hadith's own chain; if none does, the two words before the verdict are kept."""
    m = NAME_FINAL.search(text)
    if not m: return None
    chain = set(norm(w) for w in re.findall(r"[ء-ي]+", isnad or "")); pre = text[:m.start(1)].split(); take = []
    for w in reversed(pre[-8:]):
        nw = norm(re.sub(r"[^ء-ي]", "", w))
        if nw in chain and nw not in NAME_PASS or (nw in NAME_PASS and take): take.append(w)
        elif nw in NAME_PASS and not take: take.append(w)
        else: break
    while take and norm(take[-1]) in ("عن", "غير", "هذا", "وهو", "هو"): take.pop()
    if not any(norm(re.sub(r"[^ء-ي]", "", w)) not in NAME_PASS for w in take): take = list(reversed(pre[-2:]))
    return " ".join(list(reversed(take)) + [m.group(1)])
NAMED_REMARK = re.compile(r"((?:\[?قال عبد الله(?: بن أحمد)?\]?\s*:?\s*)?قال (?:أبو داود|أبو عيسى|أبو عبد الرحمن|أبو بكر|أبو الحسن|أبو محمد|أبو حاتم|أبي|عبد الله|الشيخ|البزار|أبو القاسم|أحمد)\s*:?.{0,500})", re.S)
UNIQ = re.compile(rf"{A}تفرد|لا نعلم\S* (?:يروي|روي|رواه|احدا)|لم يرو\S* |لا يروي |{A}غريب{Z}")
DEFECT = re.compile(rf"{A}و?خالفه|الصواب|{A}اصح{Z}|{A}وهم{Z}|غير محفوظ|موقوف|اختلف (?:فيه|علي)|ان صح الخبر|في القلب من|لست اعرف|لا اعرف|ابرا من عهده|خطا")
TAIL_COLLS = {"0385Daraqutni.Sunan", "0458Bayhaqi.ShucabIman", "0311IbnKhuzaymaNaysaburi.Sahih", "0303Nasai.SunanKubra", "0303Nasai.SunanSughra"}


def remarks(repo):
    rows = []; per = collections.defaultdict(collections.Counter)
    for c in all_cols(repo):
        if c in ("0256Bukhari.Sahih", "0261Muslim.Sahih"): continue          # their remarks are not about the standing of their own hadith
        who, death = COMPILER.get(c, (c, ""))
        for h in J(os.path.join(repo, f"apparatus/hadith/{c}.jsonl.gz")):
            text = h.get("matn") or h.get("isnad") or ""
            found = [x for x in (h.get("comments") or [])]
            for m in NAMED_REMARK.finditer(text):
                if not any(m.group(1)[:40] in f or f[:40] in m.group(1) for f in found): found.append(m.group(1))
            if c in TAIL_COLLS and len(text) > 40:
                tail = text[max(len(text) // 2, len(text) - 600):]
                m = TAIL_REMARK.search(tail)
                got = m.group(1) if m else name_final(text, h.get("isnad"))
                if got and not any(got[:30] in f or got in f for f in found): found.append(got)
            seen = set()
            for f in found:
                f = re.sub(r"\s*\|?\s*\d+\s*\(\s*(?:\d+\s*)?(?:باب|من اسمه|ذكر|كتاب|مسند|حديث|ومن|ما |في ).*$", "", clean(f)).strip()          # a chapter heading that follows in the source
                if len(f) < 8 or f[:50] in seen: continue
                seen.add(f[:50]); n = norm(f); cls = classify(f)
                if cls == "unclassified":
                    cls = "uniqueness" if UNIQ.search(n) else "defect_note" if DEFECT.search(n) else None
                elif cls in ("weak",) and UNIQ.search(n) and not re.search(rf"{A}(?:ضعيف|ضعف|منكر|لا يصح|لا يثبت|مرسل|منقطع){Z}", n): cls = "uniqueness"
                if not cls: continue
                if cls in ("sound", "fair") and any(g.get("method") == "inline" for g in h.get("grades") or []): continue   # already his grade in the layer
                rows.append({"hadith_id": h["id"], "critic": f"{who} (his own remark)", "death_ah": death, "layer": "classical",
                             "scope": scope_of(f), "class": cls, "verdict": f[:600], "match": 1.0, "candidates": 1,
                             "critic_record": (h.get("source_ids") or [""])[-1], "loc": "", "entry": h.get("number"), "sources": who,
                             "quoted": (h.get("matn") or "")[:160]})
                per[c][cls] += 1
    s = write(repo, "apparatus/hadith_grades/compilers_remarks.tsv", rows)
    s["by_collection"] = {k: dict(v) for k, v in sorted(per.items())}
    return s


# ---------- 3. the Sahih wording note, wider ----------
def insahih(repo):
    SAHIH = [C_ for C_ in ("0256Bukhari.Sahih", "0261Muslim.Sahih")]
    S = B.Layer(repo, SAHIH, "matn"); S_ID = {h["id"]: k for k, h in enumerate(S.h)}
    group = {}
    with gzip.open(os.path.join(repo, "apparatus/hadith_links/parallels.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"): group[r["hadith_id"]] = r["group"]
    mund = collections.defaultdict(list)       # a critic says so: 'أخرجه البخاري ومسلم' (al-Mundhiri, al-Nawawi, Ibn Hajar)
    gd = os.path.join(repo, "apparatus/hadith_grades")
    for p in sorted(os.listdir(gd)):
        for r in csv.DictReader(open(os.path.join(gd, p), encoding="utf-8"), delimiter="\t"):
            if r.get("hadith_id") and r.get("class") == "in_sahihayn" and r["candidates"] == "1": mund[r["hadith_id"]].append(r)
    out = B.__dict__.get("gzw")
    path = os.path.join(repo, "apparatus/hadith_links/in_sahih.tsv.gz"); per = collections.Counter(); st = collections.Counter()
    fz = open(path, "wb"); gz = gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename=""); f = io.TextIOWrapper(gz, encoding="utf-8", newline="\n")
    f.write("hadith_id\tbukhari\tmuslim\toverlap\tparallel_group\tcompanion\tbasis\tcritic_record\n")
    for c in all_cols(repo):
        if c in SAHIH: continue
        for h in J(os.path.join(repo, f"apparatus/hadith/{c}.jsonl.gz")):
            s = shingles(toks(h.get("matn") or "")); best = {}
            if len(s) >= 4:
                votes = collections.Counter()
                for x in s:
                    Lx = S.idx.get(x, ())
                    if len(Lx) > 3000: continue
                    for k in Lx: votes[k] += 1
                for k, v in votes.most_common(30):
                    o = v / min(len(s), len(S.sh[k]))
                    if v >= 4 and len(S.sh[k]) >= 4 and o >= 0.6: best[k] = min(o, 1.0)
            g = group.get(h["id"], ""); mrow = mund.get(h["id"])
            if not best and not mrow: continue
            narr = B.name_tokens(h.get("narrator") or "")
            keep = []
            for k, o in sorted(best.items(), key=lambda kv: -kv[1]):
                sh_ = S.h[k]; same = B.same_narrator(narr, sh_)
                comp = "same" if same else "other" if same is False else "unknown"
                keep.append((sh_["id"], o, comp, group.get(sh_["id"]) == g and bool(g)))
            # a wording match under another Companion is kept only when the wording is nearly identical
            keep = [x for x in keep if x[2] != "other" or (x[1] >= 0.8 and min(len(s), len(S.sh[S_ID[x[0]]])) >= 8)]
            if not keep and not mrow: continue
            comp = "same" if any(x[2] == "same" for x in keep) else "unknown" if any(x[2] == "unknown" for x in keep) else "other" if keep else ""
            pick = [x for x in keep if x[2] == comp] or keep
            b = [x[0] for x in pick if "Bukhari" in x[0]][:3]; mu = [x[0] for x in pick if "Muslim" in x[0]][:3]
            basis = [w for w, ok in (("parallel_group", any(x[3] for x in pick)), ("wording", bool(pick) and not any(x[3] for x in pick)),
                                     ("critic_takhrij", bool(mrow))) if ok]
            f.write("\t".join([h["id"], ";".join(b), ";".join(mu), str(round(max((x[1] for x in pick), default=0), 2)) if pick else "", g,
                               comp, "+".join(basis), mrow[0]["critic_record"] if mrow else ""]) + "\n")
            per[c] += 1; st["companion_" + (comp or "none")] += 1
            for w in basis: st["basis_" + w] += 1
    f.close(); fz.close()
    return {"file": "apparatus/hadith_links/in_sahih.tsv.gz", "hadith_with_wording_in_sahih": sum(per.values()), **dict(st), "by_collection": dict(per),
            "note": "companion = same: the hadith's Companion is in the Sahih hadith's chain. other: the wording is in the Sahih from another Companion (kept only at 80% overlap of a wording of some length). A note on the wording, never a grade of this chain."}


# ---------- 4. weak narrators in the chains of hadith that have no grade ----------
def graded_ids(repo):
    own, crit = set(), set()
    for c in all_cols(repo):
        for r in J(os.path.join(repo, f"apparatus/hadith/{c}.jsonl.gz")):
            if r.get("grades"): own.add(r["id"])
    gd = os.path.join(repo, "apparatus/hadith_grades")
    for p in sorted(os.listdir(gd)):
        for r in csv.DictReader(open(os.path.join(gd, p), encoding="utf-8"), delimiter="\t"):
            if r.get("hadith_id") and (r.get("class") is None or r["class"] in GRADE_CLASSES): crit.add(r["hadith_id"])
    return own, crit


def narrators(repo):
    own, crit = graded_ids(repo); uid = {}
    with gzip.open(os.path.join(repo, "apparatus/rijal/taqrib_index.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"): uid[r["taqrib_no"]] = r["corpus_uid"]
    path = os.path.join(repo, "apparatus/hadith_links/weak_links.tsv.gz"); st = collections.Counter()
    fz = open(path, "wb"); gz = gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename=""); f = io.TextIOWrapper(gz, encoding="utf-8", newline="\n")
    f.write("hadith_id\tnarrator_in_chain\ttaqrib_no\ttaqrib_name\tibn_hajar_grade\trank\tlink_method\tlinked\tnames\ttaqrib_record\n")
    for c in J(os.path.join(repo, "apparatus/hadith_links/chains.jsonl.gz")):
        h = c["hadith_id"]; g = h in own or h in crit
        st["hadith"] += 1; st["ungraded"] += not g
        weak = [n for n in c["narrators"] if n.get("rank") and n["rank"] >= 8 and len(n["name"].split()) >= 3]
        if not g:
            st["ungraded_with_weak_narrator"] += bool(weak)
            st["ungraded_fully_linked_all_reliable"] += bool(c["names"]) and c["linked"] == c["names"] and (c["weakest_rank"] or 99) <= 4
        for n in ([] if g else weak):
            f.write("\t".join(map(str, [h, n["name"], n["taqrib_no"], n["taqrib_name"], n["grade"], n["rank"], n["match"], c["linked"], c["names"],
                                        uid.get(str(n["taqrib_no"]), "")])) + "\n")
            st["rows"] += 1
    f.close(); fz.close()
    return {"file": "apparatus/hadith_links/weak_links.tsv.gz", **dict(st),
            "note": "only hadith with no classical grade; only narrators named with at least three words (a bare kunya or a short name is too often linked to a namesake). Rank 8-12 on Ibn Hajar's scale (da'if, majhul, matruk, muttaham, kadhdhab). Evidence about one narrator, not a grade of the hadith: the link is automatic, and corroboration and hidden defects are not weighed."}


# ---------- 5. the modern column ----------
EDITIONS = {
    "arnaut_ahmad": {"version": "0241IbnHanbal.Musnad.ShamAY0033964-ara2", "collection": "0241IbnHanbal.Musnad", "sources": "Ahmad",
                     "critic": "Shuʿayb al-Arnaʾut (notes on Ahmad's Musnad, Qurtuba printing)", "death_ah": 1438,
                     "marker": r"تعليق شعيب الأرنؤوط\s*:", "numbers": False},
    "husayn_asad_darimi": {"version": "0255CabdAllahDarimi.Sunan.ShamAY0033928-ara1", "collection": "0255CabdAllahDarimi.Sunan", "sources": "al-Darimi",
                           "critic": "Husayn Salim Asad (notes on al-Darimi's Sunan)", "death_ah": 1443, "marker": r"قال حسين سليم أسد\s*:", "numbers": True},
    "husayn_asad_abuyacla": {"version": "0307AbuYaclaMawsili.Musnad.Shamela0012520-ara1", "collection": "0307AbuYaclaMawsili.Musnad", "sources": "Abu Yaʿla",
                             "critic": "Husayn Salim Asad (notes on Abu Yaʿla's Musnad)", "death_ah": 1443, "marker": r"\[حكم حسين سليم أسد\]\s*:?", "numbers": True},
}
PINS = "catalogs/modern_editions_pins.json"


def fetch_editions(repo, meta):
    import subprocess
    by = {r["versionUri"]: r for r in csv.DictReader(open(meta, encoding="utf-8"), delimiter="\t")}
    pins, heads = {}, {}
    for key, e in EDITIONS.items():
        v = by[e["version"]]; m = re.match(r"https://raw.githubusercontent.com/OpenITI/([^/]+)/[^/]+/(.+)$", v["url"]); rp, path = m.group(1), m.group(2)
        if rp not in heads: heads[rp] = subprocess.check_output(["git", "ls-remote", f"https://github.com/OpenITI/{rp}.git", "HEAD"], text=True).split()[0]
        raw = urllib.request.urlopen(f"https://raw.githubusercontent.com/OpenITI/{rp}/{heads[rp]}/{path}", timeout=300).read()
        pins[key] = {"version": e["version"], "repo": rp, "commit": heads[rp], "path": path, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                     "edition": v["ed_info"], "use": "the editor's verdict lines only; not a corpus work, not searched"}
        out = os.path.join(repo, "sources/openiti/modern_editions", e["version"] + ".gz"); os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0, filename="") as g: g.write(raw)
        print("pinned", e["version"], len(raw), flush=True)
    json.dump({"source": "OpenITI (github.com/OpenITI), CC BY-NC-SA 4.0", "works": pins}, open(os.path.join(repo, PINS), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def edition(repo, key):
    e = EDITIONS[key]; pins = json.load(open(os.path.join(repo, PINS), encoding="utf-8"))["works"][key]
    raw = gzip.open(os.path.join(repo, "sources/openiti/modern_editions", e["version"] + ".gz")).read()
    if hashlib.sha256(raw).hexdigest() != pins["sha256"]: sys.exit("sha256 mismatch: " + e["version"])
    body = raw.decode("utf-8").split("#META#Header#End#", 1)[-1]
    L = layer(repo); by_no = L.numbers(); col = e["collection"]; MARK = re.compile(e["marker"]); NUM = re.compile(r"^(?:### \|+\s*|# |~~)?\s*(\d+)\s*-\s")
    rows = []; buf = []; no = ""; vol = page = ""; want = 0; verdict = None
    def done():
        nonlocal buf, verdict
        if verdict is None: return
        v = clean(re.sub(r"<[^>]+>", " ", verdict)).strip(" :"); text = clean(" ".join(buf))
        if v and len(v) <= 700 and text:
            base = {"critic": e["critic"], "death_ah": e["death_ah"], "layer": "modern", "scope": scope_of(v), "class": classify(v), "verdict": v[:600],
                    "critic_record": f"{e['version']}#{no}", "loc": f"{vol}:{page}" if page else "", "entry": no, "sources": e["sources"], "quoted": text[:160]}
            cands = L.match(text, only={col}, thr=0.5)
            if e["numbers"]:
                agree = [c for c in cands if str(c[1]["number"]) == no]
                cands = agree or ([c for c in cands if c[0] >= 0.8] if len(cands) == 1 else [])
            emit(rows, base, cands)
        buf = []; verdict = None
    for line in body.splitlines():
        for m in B.PAGE.finditer(line): vol, page = int(m.group(1)), int(m.group(2))
        l = B.PAGE.sub(" ", line)
        if MARK.search(l):
            verdict = MARK.split(l, 1)[1]; want = 3; continue
        m = NUM.match(l)
        if m and (verdict is not None or not buf or l.startswith("###")):
            done(); buf = []; no = m.group(1); l = l[m.end():]
        elif verdict is not None and want and re.match(r"^(?:# |~~)", l) and "book-container" not in l and l.strip("#~ "):
            verdict += " " + l[2:]; want -= 1; continue
        if l.startswith("###"): continue
        t = re.sub(r"^(?:# |~~)", "", l).strip()
        if t and "book-container" not in t and verdict is None: buf.append(t)
    done()
    return write(repo, f"apparatus/hadith_grades_modern/{key}.tsv", rows)


def albani_jami(repo):
    L = layer(repo); rows = []; recs = list(J(os.path.join(repo, "corpus/modern/0911Suyuti.SahihWaDacif.jsonl.gz")))
    NOT_SAHIH = set(all_cols(repo)) - {"0256Bukhari.Sahih", "0261Muslim.Sahih"}
    no = ""; quote = None
    for i, r in enumerate(recs):
        raw = raw_of(r)
        if r.get("kind") == "heading":
            m = re.search(r"\|\s*(\d+)\s*-", raw)
            if m: no = m.group(1); quote = None
            elif "حكم الألباني" in raw and quote and i + 1 < len(recs):
                v = clean(raw_of(recs[i + 1]))
                if not v or len(v) > 300: continue
                base = {"critic": "al-Albani (Sahih wa-daʿif al-Jamiʿ al-saghir)", "death_ah": 1420, "layer": "modern", "scope": "hadith",
                        "class": classify(re.sub(r"انظر.*$", "", v)), "verdict": v, "critic_record": recs[i + 1]["id"], "loc": "", "entry": no,
                        "sources": "", "quoted": quote[:160]}
                cands = L.match(quote, only=NOT_SAHIH, thr=0.7, min_hits=5)
                qs = shingles(toks(quote))
                cands = [c for c in cands if len(qs & shingles(toks(c[1].get("matn") or ""))) >= 5]
                emit(rows, base, cands)
            continue
        if quote is None and no: quote = clean(raw)
    rows = [o for o in rows if o["hadith_id"]]            # the unjoined entries are already in apparatus/sayings/sayings_modern.tsv.gz
    return write(repo, "apparatus/hadith_grades_modern/albani_jami.tsv", rows)


def modern(repo):
    out = {k: edition(repo, k) for k in EDITIONS}
    out["albani_jami"] = albani_jami(repo)
    return out


# ---------- coverage ----------
def coverage(repo):
    own, crit = graded_ids(repo); coll = {}
    for c in all_cols(repo):
        for r in J(os.path.join(repo, f"apparatus/hadith/{c}.jsonl.gz")): coll[r["id"]] = c
    sah = set()
    with gzip.open(os.path.join(repo, "apparatus/hadith_links/in_sahih.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r.get("companion", "same") != "other": sah.add(r["hadith_id"])
    mod = set(); md = os.path.join(repo, "apparatus/hadith_grades_modern")
    for p in sorted(os.listdir(md)):
        for r in csv.DictReader(open(os.path.join(md, p), encoding="utf-8"), delimiter="\t"):
            if r.get("hadith_id") and r["class"] in GRADE_CLASSES: mod.add(r["hadith_id"])
    per = collections.defaultdict(collections.Counter)
    for h, c in coll.items():
        g = h in own or h in crit
        per[c]["hadith"] += 1; per[c]["compiler_grade"] += h in own; per[c]["critic_verdict"] += h in crit
        per[c]["no_classical_grade"] += not g; per[c]["nothing_at_all"] += not g and h not in sah
        per[c]["modern_grade"] += h in mod; per[c]["no_grade_classical_or_modern"] += not g and h not in mod
    tot = collections.Counter()
    for v in per.values(): tot.update(v)
    return {"collections": len(per), **dict(tot), "by_collection": {k: dict(v) for k, v in sorted(per.items())},
            "note": "classical grade = the compiler's own, or a critic's verdict joined as data (a remark that only notes uniqueness or a difference between narrators is not counted; nor is 'he says al-Bukhari reported it'). The Sahih wording note and the modern column are not classical grades. v47 counts with whole-word classes."}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", nargs="*", default=["all"]); ap.add_argument("--repo", default=".")
    ap.add_argument("--fetch", help="OpenITI metadata csv: fetch and pin the three modern editions first")
    a = ap.parse_args()
    if a.fetch: fetch_editions(a.repo, a.fetch)
    jobs = {"critics": critics, "remarks": remarks, "insahih": insahih, "narrators": narrators, "modern": modern, "coverage": coverage}
    todo = list(jobs) if "all" in a.what else a.what
    sp = os.path.join(a.repo, "catalogs/critic_grades_summary.json")
    summary = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    for k in todo:
        res = jobs[k](a.repo)
        summary["insahih" if k == "insahih" else "coverage" if k == "coverage" else "v47_" + k] = res
        print(k, json.dumps(res, ensure_ascii=False)[:2500], flush=True)
    json.dump(summary, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
