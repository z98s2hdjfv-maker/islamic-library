#!/usr/bin/env python3
"""
build_hadith_layer_extra.py - v46: the eight collections of corpus/hadith_extra (v45) as hadith-level records,
in the same form as build_hadith_layer.py (v16) and beside its output: apparatus/hadith/<collection>.jsonl.gz.
The thirteen collections of v16 are not touched.

  al-Tayalisi, al-Humaydi, Abu Ya'la, al-Tabarani's Awsat and Saghir, al-Bayhaqi's Shu'ab
        JK texts: the edition's number opens each hadith, as in al-Tabarani's Kabir.
  al-Bazzar (al-Bahr al-zakhkhar)
        the number is a heading ("### | 387 -"); page headings ("[ص: 40]") fall inside a hadith and are skipped.
        al-Bazzar's own remark after the hadith ("وهذا الحديث لا نعلمه يروى ... إلا من هذا الوجه") goes to `comments`.
  Ibn Hibban's Sahih, in Ibn Balban's arrangement (al-Ihsan)
        "4555 - أخبرنا ..." or "[497] أخبرنا ..." (this source text prints some hadith twice: the repeat is
        skipped); the modern editor's footnotes (a paragraph opening with a bare
        footnote number) end the hadith and are NOT taken into it, so no modern grading enters.
        Grade: Ibn Hibban's own claim of soundness by inclusion (he is counted among the lenient).

Everything is derived automatically and marked status="unverified".
Usage: build_hadith_layer_extra.py [--repo .]
"""
import argparse, collections, gzip, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_hadith_layer as B  # noqa: E402

JK = {"0204AbuDawudTayalisi.Musnad": "edition numbering of the JK text",
      "0219IbnZubayrHumaydi.Musnad": "edition numbering of the JK text",
      "0307AbuYaclaMawsili.Musnad": "edition numbering of the JK text (Husayn Salim Asad)",
      "0360Tabarani.MucjamAwsat": "edition numbering of the JK text",
      "0360Tabarani.MucjamSaghir": "edition numbering of the JK text",
      "0458Bayhaqi.ShucabIman": "edition numbering of the JK text"}
OTHER = {"0292AbuBakrBazzar.BahrZakhkhar": "edition numbering of the Shamela text (number in the heading)",
         "0739CalaDinIbnBalban.Ihsan": "edition numbering of al-Ihsan (Ibn Balban's arrangement of Ibn Hibban's Sahih)"}
GRADE = {"0739CalaDinIbnBalban.Ihsan": ("Ibn Hibban", "sahih (compiler's own claim, by inclusion in his Sahih; counted among the lenient)")}
REMARK = re.compile(r"\s((?:و)?(?:هذا الحديث|هذا الكلام|هذه الأحاديث|هذا الإسناد|لا نعلم(?:ه)?|لم يرو هذا|لم يروه|لا يروى هذا|تفرد به)\s.*)$", re.S)
B.EDITION.update(JK)


def clean(r):
    return re.sub(r"^\s*#+\s*\$+\s*", "", r.get("text") or "")


def bazzar(path):
    cur = None; seq = 0
    for line in gzip.open(path, "rt", encoding="utf-8"):
        r = json.loads(line)
        if r["kind"] == "heading":
            m = re.search(r"\|\s*(\d+)\s*-", r.get("text_raw") or "")
            if m:
                if cur: yield cur
                seq += 1; cur = {"n": int(m.group(1)), "seq": seq, "ids": [], "text": "", "heads": []}
            continue
        t = clean(r)
        if cur is not None and t: cur["ids"].append(r["id"]); cur["text"] = (cur["text"] + " " + t).strip()
    if cur: yield cur


def ihsan(path):
    START = re.compile(r"^\s*(?:\[(\d{1,5})\]|(\d{1,5})\s*-)\s*(?=" + B.VERB + r"|ح?دثنا|سمعت|قال|وأخبرنا)")
    FOOT = re.compile(r"^\s*\d{1,2}\s+\S|^[.\s…]+$")
    cur = None; seq = 0; heads = []; closed = True; first = {}
    for line in gzip.open(path, "rt", encoding="utf-8"):
        r = json.loads(line)
        if r["kind"] == "heading":
            heads = [re.sub(r"^#+\s*\|+\s*(AUTO)?\s*", "", r.get("text_raw") or "").strip()]; continue
        t = clean(r)
        if not t: continue
        m = START.match(t)
        if m:
            n = int(m.group(1) or m.group(2)); key = re.sub(r"\W", "", t[m.end():])[:40]
            if first.get(n) == key: closed = True; continue      # this source text prints some hadith twice ("497 -" and "[497]")
            first.setdefault(n, key)
            if cur: yield cur
            seq += 1; closed = False
            cur = {"n": n, "seq": seq, "ids": [r["id"]], "text": t[m.end():], "heads": list(heads)}
        elif FOOT.match(t) or re.match(r"^\d+\s*-\s*باب", t): closed = True       # editor's footnote or a chapter line
        elif cur and not closed:
            cur["ids"].append(r["id"]); cur["text"] += " " + t
    if cur: yield cur


def build(repo):
    out_dir = os.path.join(repo, "apparatus/hadith")
    sp = os.path.join(repo, "catalogs/hadith_layer_summary.json"); summary = json.load(open(sp, encoding="utf-8"))
    for book, numbering in {**JK, **OTHER}.items():
        path = os.path.join(repo, "corpus/hadith_extra", book + ".jsonl.gz")
        if not os.path.exists(path): print("missing", path); continue
        gen = B.units(path, book) if book in JK else bazzar(path) if "Bazzar" in book else ihsan(path)
        stats = collections.Counter(); caliph = collections.Counter(); comp = collections.Counter(); seen = set()
        with open(os.path.join(out_dir, book + ".jsonl.gz"), "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
             io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
            for u in gen:
                text = B.TAILNUM.sub("", u["text"]).strip()
                if "Ihsan" in book:      # footnote calls and the editor's cross-reference codes
                    text = re.sub(r"\(¬\d+\)|\[\d+\s*:\s*\d+\]", "", text)
                    text = re.sub(r"(?<=[\"”»])\s?\d{1,2}(?=[.،\s]|$)", "", text).strip(" .")
                if not text or not u["ids"]: continue
                comments = []
                if "Bazzar" in book or "Awsat" in book or "Saghir" in book:
                    m = REMARK.search(text)
                    if m and m.start() > 20: comments = [m.group(1).strip()[:600]]; text = text[:m.start()].strip()
                isnad, matn, how = B.split(text)
                n = u["n"]
                if n in seen: n = f"{u['n']}#{u['seq']}"
                seen.add(n)
                c = B.narrator(isnad) if isnad else None
                cal = B.CALIPHS.get(c) if c else None
                grades = [{"by": GRADE[book][0], "grade": GRADE[book][1], "method": "collection"}] if book in GRADE else []
                rec = {"id": f"urn:hadith:{book}:{n}", "collection": book, "number": n, "numbering": "edition",
                       "chapter": u["heads"][-1] if u["heads"] else None, "isnad": isnad, "matn": matn, "split_method": how,
                       "narrator": c, "caliph": cal, "grades": grades,
                       "comments": comments or [m.group(1).strip() for m in B.COMMENT.finditer(matn)][:5],
                       "source_ids": u["ids"], "status": "unverified"}
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stats["hadith"] += 1; stats["split_" + how] += 1; stats["with_narrator"] += bool(c); stats["with_remark"] += bool(comments)
                if cal: caliph[cal] += 1
                if c: comp[c] += 1
        summary["collections"][book] = {"numbering": numbering, **stats, "caliphs": dict(caliph), "top_narrators": comp.most_common(10), "added": "v46"}
        print(book, dict(stats), flush=True)
    tot = collections.Counter()
    for v in summary["collections"].values():
        for k in ("hadith", "with_narrator", "inline_grades"): tot[k] += v.get(k, 0)
        for k, x in v["caliphs"].items(): tot["caliph_" + k] += x
    summary["totals"] = dict(tot)
    json.dump(summary, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); build(ap.parse_args().repo)
