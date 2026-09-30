#!/usr/bin/env python3
"""
build_names_table.py - v26: the 99 Beautiful Names as a table that joins the library together.

Source of the list: the one narration that enumerates the names, al-Tirmidhi, Jami (JK edition record
p09314, Abu Hurayra via al-Walid b. Muslim). Its wording is taken from the corpus, never retyped.
Al-Tirmidhi himself grades it "gharib" and notes that no other chain listing the names is sound; the number
"99, whoever enumerates them enters Paradise" is in al-Bukhari and Muslim without the list. Whether the list is
the Prophet's words or a narrator's addition is discussed in Ibn Hajar's Takhrij (corpus/asma).

Output reports/asma/names.tsv, one row per name:
  n, name, quran_verses (verses containing the word form, with or without al- and the prefixes w/f/b/l;
  a form count, not a count of uses as a divine name: al-haqq or al-ali also have ordinary uses),
  quran_first (sura:aya), ghazali_record and ghazali_page (the heading of that name in al-Ghazali's
  al-Maqsad al-asna, corpus/asma), qurtubi_units (units of al-Qurtubi's al-Asna naming it).
Ibn Arabi treats the names one "presence" (hadra) at a time in Futuhat ch. 558:
corpus/ibnarabi/futuhat.arabiyya records r02226-r02360 (Cairo ed. IV:196-326).
Usage: python3 pipeline/asma/build_names_table.py --repo .
"""
import argparse, csv, gzip, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from textnorm import norm  # noqa: E402

MULTI = [("مالك", "الملك"), ("ذو", "الجلال", "والاكرام")]


def names_from_tirmidhi(repo):
    for l in gzip.open(os.path.join(repo, "corpus/hadith/0279Tirmidhi.Sunan.jsonl.gz"), "rt", encoding="utf-8"):
        r = json.loads(l)
        if r.get("id", "").endswith(":p09314"):
            t = norm(r["text"])
            seg = t.split("لا اله الا هو", 1)[1].split("قال ابو عيسي", 1)[0]
            toks, out, i = seg.split(), ["الله"], 0
            while i < len(toks):
                for m in MULTI:
                    if tuple(toks[i:i + len(m)]) == m: out.append(" ".join(m)); i += len(m); break
                else: out.append(toks[i]); i += 1
            return out, r["id"]
    raise SystemExit("Tirmidhi p09314 not found")


def main(repo):
    names, src = names_from_tirmidhi(repo)
    quran = [(r["sura"], r["aya"], set(norm(r["text"]).split()))
             for r in map(json.loads, gzip.open(os.path.join(repo, "corpus/quran/0001Quran.Mushaf.jsonl.gz"), "rt", encoding="utf-8"))]
    gh = [json.loads(l) for l in gzip.open(os.path.join(repo, "corpus/asma/0505Ghazali.MaqsadAsna.jsonl.gz"), "rt", encoding="utf-8")]
    qu = [norm(json.loads(l).get("text") or "") for l in gzip.open(os.path.join(repo, "corpus/asma/0671AbuCabdAllahQurtubi.Asna.jsonl.gz"), "rt", encoding="utf-8")]
    rows = []
    for n, name in enumerate(names):
        if " " in name:
            words = name.split(); vs = [(s, a) for s, a, w in quran if all(x in w for x in words)]
        else:
            base = name[2:] if name.startswith("ال") and name != "الله" else name
            forms = {name, base} | {p + f for f in (name, base) for p in ("و", "ف", "ب", "ل")}
            if name == "الله": forms |= {"لله", "ولله", "فلله", "بالله", "والله", "تالله", "اللهم"}
            vs = [(s, a) for s, a, w in quran if w & forms]
        # Ghazali heads a name, or a pair of names, with a short unit of its own ("القدوس", "القابض الباسط")
        alias = {name, {"الرءوف": "الرووف"}.get(name, name)}
        def toks(r):
            ws = norm(r.get("text") or "").replace("|", " ").split()
            return ws, {w[1:] if w.startswith("وال") else w for w in ws}
        heads = [r for r in gh if 0 < len(toks(r)[0]) <= 4]
        g = (next((r for r in heads if " ".join(toks(r)[0]) in alias), None) or
             next((r for r in heads if (" " in name and name in " ".join(toks(r)[0])) or
                   (" " not in name and alias & toks(r)[1] and "مالك" not in toks(r)[0])), None) or
             next((r for r in gh if name != "الله" and norm(r.get("text") or "").startswith(name + " هو")), None))
        qn = sum(1 for t in qu if name in t)
        rows.append([n, name, len(vs), f"{vs[0][0]}:{vs[0][1]}" if vs else "", g["id"] if g else "", g.get("page_before", "") if g else "", qn])
    out = os.path.join(repo, "reports/asma"); os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "names.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["n", "name", "quran_verses", "quran_first", "ghazali_record", "ghazali_page", "qurtubi_units"])
        w.writerows(rows)
    print(len(names) - 1, "names after Allah, from", src, "| Ghazali headings found:", sum(1 for r in rows if r[4]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); main(ap.parse_args().repo)
