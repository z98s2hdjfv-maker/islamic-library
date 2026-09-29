#!/usr/bin/env python3
"""
build_chittick_concordance.py - v25: map William Chittick's "Me & Rumi" (2004) to our OCR of Movahhed's
edition of Shams's Maqalat, by Chittick's page citations only. The book is copyrighted and is NOT in the repo;
run this locally against your own copy. The output stores numbers only, never Chittick's text.

Chittick cites Movahhed (Tehran: Khwarazmi, 1369/1990) by one running page number, e.g. "(699)" or "(192-93)".
Our OCR (4th printing, 1391/2012) has two volumes with separate pagination. Tested model:
  cited page <= 597  -> vol. 1, same page      (checked: (299) = vol. 1 p. 299, the Ibn Arabi passage)
  cited page  > 597  -> vol. 2, page - 597     (checked: (697-98) = vol. 2 p. 100, the Khidr passage)
archive.org's printed_page in our OCR runs one ahead of the number printed in the page header, so the
record for printed page N is the one with printed_page N+1 (checked on vol. 1 p. 299 and vol. 2 pp. 51, 100).
Citations may be off by one where a passage runs across pages: ocr_record_next gives the following page.

Output: reports/concordance/chittick_movahhed.tsv
  chittick_pdf_page, movahhed_ref_as_cited, movahhed_vol, movahhed_page_in_vol, ocr_record, ocr_record_next
Usage: python3 build_chittick_concordance.py --pdf "Me and Rumi.pdf" --repo .
Needs pdftotext (poppler-utils).
"""
import argparse, csv, json, os, re, subprocess

FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
REF = re.compile(r"\((\d{1,3}(?:-\d{1,3})?(?:,\s*\d{1,3}(?:-\d{1,3})?)*)\)")


def main(pdf, repo):
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    byfield, vol, prev = {}, 1, 0
    for l in open(os.path.join(repo, "corpus/shams/maqalat.movahhed_ocr.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        try: p = int(str(r.get("printed_page")).translate(FA))
        except ValueError: continue
        if p < prev - 20: vol = 2
        prev = p; byfield.setdefault((vol, p), r["id"])
    rows = []
    for pi, pg in enumerate(text.split("\f"), 1):
        if pi < 20: continue  # front matter
        for m in REF.finditer(pg):
            first = int(re.findall(r"\d+", m.group(1))[0])
            v, tp = (1, first) if first <= 597 else (2, first - 597)
            rows.append([pi, m.group(1), v, tp, byfield.get((v, tp + 1), ""), byfield.get((v, tp + 2), "")])
    out = os.path.join(repo, "reports/concordance"); os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "chittick_movahhed.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["chittick_pdf_page", "movahhed_ref_as_cited", "movahhed_vol", "movahhed_page_in_vol", "ocr_record", "ocr_record_next"])
        w.writerows(rows)
    print(len(rows), "citations")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pdf", required=True); ap.add_argument("--repo", default=".")
    a = ap.parse_args(); main(a.pdf, a.repo)
