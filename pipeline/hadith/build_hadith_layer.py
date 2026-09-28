#!/usr/bin/env python3
"""
build_hadith_layer.py - v16: a hadith-level layer over corpus/hadith/ (v15).

Turns the paragraph records of each collection into one record per hadith:
  id           urn:hadith:<collection>:<number>
  number       the edition's own number where the text carries one (numbering="edition", named per
               collection below), otherwise a running count made here (numbering="sequential")
  isnad, matn  split at the '*' marker of the JK/OpenITI editions, else at the first mention of the
               Prophet (split_method says which)
  narrator     the last narrator in the isnad: normally the Companion who heard the Prophet; for reports
               that stop at a Companion or Successor it is that authority (heuristic, read from the isnad text;
               may be unresolved, e.g. "abihi")
  caliph       Abu Bakr / Umar / Uthman / Ali when that narrator is named as one of them (heuristic)
  grades       only grades that are in the sources themselves:
                 - collection-level: al-Bukhari and Muslim (sahih by inclusion), Ibn Khuzayma (his own claim)
                 - inline: al-Tirmidhi's and al-Hakim's verdicts ("hadha hadith ...")
               No modern grades (al-Albani, al-Arna'ut) are invented or imported.
  comments     the compiler's own remarks after the matn (qala Abu Dawud / Abu Isa / ...)
  source_ids   the corpus paragraph ids the hadith was assembled from

Everything here is derived automatically and marked status="unverified".
Output: apparatus/hadith/<collection>.jsonl.gz, catalogs/hadith_layer_summary.json
Usage: build_hadith_layer.py [--repo .]
"""
import argparse, collections, glob, gzip, io, json, os, re

EDITION = {  # numbering carried in the OpenITI text, and whose it is
    "0256Bukhari.Sahih": "edition numbering of the JK text (al-Bugha, 7,124), not the Fath al-Bari 7,563",
    "0275AbuDawudSijistani.Sunan": "edition numbering (Muhyi al-Din Abd al-Hamid, 5,274)",
    "0273IbnMaja.Sunan": "edition numbering (Abd al-Baqi, 4,341)",
    "0303Nasai.SunanSughra": "edition numbering (Abu Ghudda, 5,758)",
    "0303Nasai.SunanKubra": "edition numbering of the JK text",
    "0255CabdAllahDarimi.Sunan": "edition numbering of the JK text",
    "0311IbnKhuzaymaNaysaburi.Sahih": "edition numbering (al-Azami)",
    "0405HakimNaysaburi.Mustadrak": "edition numbering of the JK text",
    "0241IbnHanbal.Musnad": "edition numbering of the Shamela text (al-Risala, 27,647)",
    "0360Tabarani.MucjamKabir": "edition numbering of the JK text",
}
EDITION.update({"0261Muslim.Sahih": "Abd al-Baqi numbering (1-3,033); each riwaya under a number is N.1, N.2, ...; muqaddima = intro.k"})
SEQUENTIAL = {"0279Tirmidhi.Sunan", "0385Daraqutni.Sunan"}   # no usable running number in text
NUMBER_LINE = {"0261Muslim.Sahih": "Abd al-Baqi numbering (number on its own line; each riwaya numbered N.1, N.2, ...)"}   # no usable running number in text
COLLECTION_GRADE = {
    "0256Bukhari.Sahih": ("al-Bukhari", "sahih (by inclusion in al-Sahih)"),
    "0261Muslim.Sahih": ("Muslim", "sahih (by inclusion in al-Sahih)"),
    "0311IbnKhuzaymaNaysaburi.Sahih": ("Ibn Khuzayma", "sahih (compiler's own claim; later critics dispute some)"),
}
INLINE_GRADER = {"0279Tirmidhi.Sunan": "al-Tirmidhi", "0405HakimNaysaburi.Mustadrak": "al-Hakim"}
VERB = r"(?:و?حدثنا|و?حدثني|و?أخبرنا|و?أخبرني|أنبأنا|ثنا|نا|أنا)"
START_NUM = re.compile(r"^\s*(\d{1,6})\s*[-–]?\s+(?=\S)")
START_VERB = re.compile(r"^\s*" + VERB + r"\b")
TAILNUM = re.compile(r"\\\s*\d+\s*\\")
PROPHET = re.compile(r"(?:عن\s+)?(?:النبي|رسول الله)\s*صلى الله عليه (?:وآله )?وسلم")
GRADE = re.compile(r"هذا (?:حديث|إسناد)\s+((?:(?:حسن|صحيح|غريب|ضعيف|منكر|مرسل|موقوف|مضطرب|مشهور)\s*)+)"
                   r"(?:\s*على شرط (?:الشيخين|البخاري|مسلم)(?: جميعا)?)?(?:\s*ولم يخرجاه)?")
COMMENT = re.compile(r"(قال (?:أبو داود|أبو عيسى|أبو عبد الرحمن|أبو بكر|أبو الحسن|الحاكم|الشيخ)[^*]{0,400})")
DIAC = re.compile(r"[\u064B-\u0652\u0670\u0640]")
CALIPHS = {"أبو بكر": "Abu Bakr", "أبو بكر الصديق": "Abu Bakr", "عمر": "Umar", "عمر بن الخطاب": "Umar",
           "عثمان": "Uthman", "عثمان بن عفان": "Uthman", "علي": "Ali", "علي بن أبي طالب": "Ali"}


def norm_name(s):
    s = DIAC.sub("", s)
    s = re.sub(r"\s*(?:رضي الله (?:عنه|عنها|عنهما|عنهم)|قال|قالت|أن|أنه|أنها|يقول|يحدث|سمعت|سمع|يرفعه|رفعه)\b.*$", "", s).strip(" ،,:.")
    s = re.sub(r"^(?:أبي|أبا)\b", "أبو", s); s = re.sub(r"^بن\b", "ابن", s)
    return {"عليا": "علي", "عمرا": "عمر"}.get(s, s)


SEPW = {"عن", "سمعت", "سمع", "أن", "أنه", "أنها", "حدثني", "حدثنا", "أخبرني", "أخبرنا", "حدثه", "أخبره", "ثنا", "نا", "أنبأنا"}


def narrator(isnad):
    t = PROPHET.split(isnad)[0] if PROPHET.search(isnad) else isnad
    words = re.sub(r"\(\d+\)", "", t).split()
    cut = [i for i, w in enumerate(words) if w.strip("،,:.") in SEPW]
    for i in reversed(cut):                    # last separator followed by a name
        name = norm_name(" ".join(words[i + 1:]))
        if 2 <= len(name) <= 40: return name
        words = words[:i]
    return None


def split(text):
    if "*" in text:
        a, b = text.split("*", 1); return a.strip(), b.strip(), "marker"
    m = PROPHET.search(text)
    if m:
        k = text.find("قال", m.end()); k = m.end() if k < 0 or k - m.end() > 12 else k + 3
        return text[:k].strip(), text[k:].strip(" :"), "prophet_mention"
    return "", text, "none"


def units(path, book):
    """Group paragraph records into hadith units."""
    cur = None; seq = 0; pending = None; sub = 0
    numline = book in NUMBER_LINE
    use_num = book in EDITION and not numline
    for line in gzip.open(path, "rt", encoding="utf-8"):
        r = json.loads(line)
        if r["kind"] == "heading":
            if cur: yield cur
            cur = None; continue
        t = re.sub(r"^\s*#+\s*\$+\s*", "", r.get("text") or "")          # OpenITI '### $' unit markers
        if book in SEQUENTIAL: t = re.sub(r"^\s*\d+\s*[-–]?\s+(?=\S)", "", t)   # per-chapter numbers (al-Daraqutni)
        if numline:   # Muslim: "(P)" = Abd al-Baqi number; "N -" lines = per-book riwaya counter (boundaries only)
            if re.match(r"^\s*\d{1,5}\s*[-–]?\s*$", t):
                if cur: yield cur
                cur = None; continue
            if not t: continue
            pm = re.match(r"^\((\d{1,5})\)\s*", t)
            if pm or START_VERB.match(t):
                if cur: yield cur
                seq += 1
                if pm:
                    p_ = int(pm.group(1)); sub = sub + 1 if p_ == pending else 1; pending = p_; t = t[pm.end():]
                    n = f"{pending}.{sub}"
                elif pending is not None:
                    sub += 1; n = f"{pending}.{sub}"
                else:
                    n = f"intro.{seq}"
                cur = {"n": n, "seq": seq, "ids": [r["id"]], "text": t, "heads": r.get("headings") or []}
            elif cur:
                cur["ids"].append(r["id"]); cur["text"] += " " + t
            continue
        m = START_NUM.match(t) if use_num else None
        starts = bool(m) or (not use_num and START_VERB.match(t))
        if starts:
            if cur: yield cur
            seq += 1
            n = int(m.group(1)) if m else seq
            cur = {"n": n, "seq": seq, "ids": [r["id"]], "text": t[m.end():] if m else t, "heads": r.get("headings") or []}
        elif cur:
            cur["ids"].append(r["id"]); cur["text"] += " " + t
    if cur: yield cur


def build(repo):
    out_dir = os.path.join(repo, "apparatus/hadith"); os.makedirs(out_dir, exist_ok=True)
    summary = {"note": "derived automatically; heuristic fields unverified", "collections": {}}
    for path in sorted(glob.glob(os.path.join(repo, "corpus/hadith/*.jsonl.gz"))):
        book = os.path.basename(path)[:-9]
        if book not in EDITION and book not in SEQUENTIAL: continue
        stats = collections.Counter(); caliph = collections.Counter(); comp = collections.Counter(); seen = set()
        out = os.path.join(out_dir, book + ".jsonl.gz")
        with open(out, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
             io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
            for u in units(path, book):
                text = TAILNUM.sub("", u["text"]).strip()
                isnad, matn, how = split(text)
                n = u["n"] if book in EDITION else u["seq"]
                if book in EDITION and n in seen: n = f"{u['n']}#{u['seq']}"   # edition repeats a number
                seen.add(n)
                c = narrator(isnad) if isnad else None
                cal = CALIPHS.get(c) if c else None
                grades = []
                if book in COLLECTION_GRADE:
                    by, g = COLLECTION_GRADE[book]; grades.append({"by": by, "grade": g, "method": "collection"})
                if book in INLINE_GRADER:
                    for gm in GRADE.finditer(matn):
                        grades.append({"by": INLINE_GRADER[book], "grade": gm.group(1).strip(), "text": gm.group(0), "method": "inline"})
                rec = {"id": f"urn:hadith:{book}:{n}", "collection": book, "number": n,
                       "numbering": "edition" if book in EDITION else "sequential",
                       "chapter": u["heads"][-1] if u["heads"] else None,
                       "isnad": isnad, "matn": matn, "split_method": how,
                       "narrator": c, "caliph": cal, "grades": grades,
                       "comments": [m.group(1).strip() for m in COMMENT.finditer(matn)][:5],
                       "source_ids": u["ids"], "status": "unverified"}
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stats["hadith"] += 1; stats["split_" + how] += 1; stats["with_narrator"] += bool(c)
                stats["inline_grades"] += sum(g["method"] == "inline" for g in grades)
                if cal: caliph[cal] += 1
                if c: comp[c] += 1
        summary["collections"][book] = {"numbering": EDITION.get(book, "sequential (made here; no number in text)"),
                                        **stats, "caliphs": dict(caliph), "top_narrators": comp.most_common(10)}
        print(book, dict(stats), dict(caliph), flush=True)
    tot = collections.Counter()
    for v in summary["collections"].values():
        for k in ("hadith", "with_narrator", "inline_grades"): tot[k] += v.get(k, 0)
        for k, x in v["caliphs"].items(): tot["caliph_" + k] += x
    summary["totals"] = dict(tot)
    json.dump(summary, open(os.path.join(repo, "catalogs/hadith_layer_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); build(ap.parse_args().repo)
