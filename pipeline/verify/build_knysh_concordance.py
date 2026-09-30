#!/usr/bin/env python3
"""
build_knysh_concordance.py - v28: map the chapters of Alexander Knysh's translation, Al-Qushayri's Epistle on
Sufism (Garnet, 2007), to our Arabic text of al-Qushayri's Risala (corpus/sufi_manuals). The translation is
copyrighted and NOT in the repo; run this locally against your own copy. The output stores only Knysh's
table-of-contents headings and page numbers, never his translation.

Method: Knysh's contents list (heading, page) and the Arabic headings (short units of the Risala: the masters'
names and the chapter terms) are both reduced to consonant skeletons (Arabic letters to Latin consonants,
long vowels dropped; Knysh's transliteration without vowels or diacritics; "b."/"ibn" dropped) and aligned in
order (Needleman-Wunsch, gaps allowed, since the Arabic edition lacks a few of Knysh's entries and vice versa).
Output: reports/concordance/knysh_risala.tsv
  knysh_heading, knysh_page, arabic_record, arabic_heading, arabic_page, score (0-1), status (matched / weak / gap)
Usage: python3 build_knysh_concordance.py --pdf Qushayri_Risala.pdf --repo .   (needs pdftotext)
"""
import argparse, csv, difflib, gzip, json, os, re, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search"))
from textnorm import norm  # noqa: E402

AR = dict(zip("بتثجحخدذرزسشصضطظغفقكلمنه", ["b", "t", "th", "j", "h", "kh", "d", "dh", "r", "z", "s", "sh", "s", "d", "t", "z", "gh", "f", "q", "k", "l", "m", "n", "h"]))
STOP = {"b", "bn", "abu", "abi", "al", "ibn"}


def skel_ar(t):
    ws = [w[2:] if w.startswith("ال") and len(w) > 3 else w for w in norm(t).split()]
    ws = [w for w in ws if w not in ("بن", "ابو", "ابي", "ومنهم")]
    return " ".join("".join(AR.get(ch, "") for ch in w) for w in ws).strip()


def skel_en(t):
    m = re.findall(r"\(([^)]*)\)", t)
    t = " ".join(m) if m else t  # a chapter: use the Arabic term in parentheses; a master: the name
    t = re.sub(r"[∏π’'`\[\].,:;-]", "", t.lower())
    ws = [re.sub(r"^al", "", w) for w in t.split() if w not in STOP]
    return " ".join(re.sub(r"[aeiouyw]", "", w).replace("ch", "sh") for w in ws).strip()


def toc(pdf):
    t = subprocess.run(["pdftotext", "-layout", "-f", "5", "-l", "22", pdf, "-"], capture_output=True, text=True).stdout
    t = t[t.find("C ONTENTS"):]; ents, buf = [], ""
    for l in (x.strip() for x in t.splitlines()):
        if not l or re.search(r"AL-QUSHAYRI’S EPISTLE|ABU .L-QASIM AL-QUSHAYRI", l): continue
        m = re.match(r"^(.*?)\s+(\d{1,3})$", l)
        if m: ents.append(((buf + " " + m.group(1)).strip(), int(m.group(2)))); buf = ""
        else: buf = (buf + " " + l).strip()
        if l.startswith("Index"): break
    start = next(i for i, e in enumerate(ents) if e[0].startswith("Chapter 1"))
    return [e for e in ents[start + 1:] if not e[0].startswith(("Glossary", "Bibliography", "Index", "Conclusion", "Chapter 2"))]


def main(pdf, repo):
    K = toc(pdf)
    A = [json.loads(l) for l in gzip.open(os.path.join(repo, "corpus/sufi_manuals/0465IbnHawazinQushayri.RisalaQushayriyya.jsonl.gz"), "rt", encoding="utf-8")]
    A = [r for r in A if (r.get("text") or "").strip().startswith("|") and 0 < len(r["text"].strip(" |").split()) <= 12]
    ks, as_ = [skel_en(k[0]) for k in K], [skel_ar(r["text"].strip(" |")) for r in A]
    sim = lambda i, j: difflib.SequenceMatcher(None, ks[i].replace(" ", ""), as_[j].replace(" ", "")).ratio()
    n, m, G = len(K), len(A), -0.2
    S = [[0.0] * (m + 1) for _ in range(n + 1)]; P = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): S[i][0] = i * G; P[i][0] = "u"
    for j in range(1, m + 1): S[0][j] = j * G; P[0][j] = "l"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            opts = [(S[i-1][j-1] + sim(i-1, j-1) - 0.35, "d"), (S[i-1][j] + G, "u"), (S[i][j-1] + G, "l")]
            S[i][j], P[i][j] = max(opts)
    i, j, rows = n, m, []
    while i or j:
        p = P[i][j]
        if p == "d": rows.append((i-1, j-1)); i, j = i-1, j-1
        elif p == "u": rows.append((i-1, None)); i -= 1
        else: j -= 1
    out = []
    for ki, aj in reversed(rows):
        if aj is None: out.append([K[ki][0], K[ki][1], "", "", "", "", "gap"]); continue
        s = sim(ki, aj); r = A[aj]
        out.append([K[ki][0], K[ki][1], r["id"], r["text"].strip(" |"), r.get("page_before", ""), f"{s:.2f}", "matched" if s >= .5 else "weak"])
    os.makedirs(os.path.join(repo, "reports/concordance"), exist_ok=True)
    with open(os.path.join(repo, "reports/concordance/knysh_risala.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["knysh_heading", "knysh_page", "arabic_record", "arabic_heading", "arabic_page", "score", "status"]); w.writerows(out)
    from collections import Counter; print(len(K), "Knysh headings,", len(A), "Arabic headings:", Counter(r[6] for r in out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pdf", required=True); ap.add_argument("--repo", default=".")
    a = ap.parse_args(); main(a.pdf, a.repo)
