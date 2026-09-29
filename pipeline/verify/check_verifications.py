#!/usr/bin/env python3
"""
check_verifications.py - validate catalogs/verification_log.tsv and summarise verification coverage.

The corpus is never edited: a passage checked against a printed edition or the scan is recorded here,
with its correction, and the original OCR stays in corpus/ untouched.

Checks every log row: the record exists in its work's corpus file, the work is in works_index.tsv,
ref_id is in catalogs/secondary_literature.tsv or is "scan" (the archive.org page image itself),
status is one of verified | corrected | disputed | illegible, and date is YYYY-MM-DD.
Output: reports/verification_summary.tsv (per work: rows by status, and OCR records scored if
reports/ocr_quality_works.tsv exists). Exits non-zero if any row fails, so a bad row stops the update.
Usage: python3 pipeline/verify/check_verifications.py --repo .
"""
import argparse, collections, csv, gzip, json, os, re, sys

STATUS = {"verified", "corrected", "disputed", "illegible"}


def main(repo):
    rd = lambda p: list(csv.DictReader(open(os.path.join(repo, p), encoding="utf-8"), delimiter="\t"))
    idx = {r["key"]: r for r in rd("catalogs/works_index.tsv")}
    refs = {r["ref_id"] for r in rd("catalogs/secondary_literature.tsv")} | {"scan"}
    log = rd("catalogs/verification_log.tsv")
    need = collections.defaultdict(set)
    for r in log: need[r["work_key"]].add(r["record_id"])
    found = {}
    for wk, ids in need.items():
        if wk not in idx: continue
        p = os.path.join(repo, idx[wk]["corpus_path"]); op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt", encoding="utf-8") as f:
            found[wk] = {json.loads(l).get("id") for l in f} & ids
    errors, summ = [], collections.defaultdict(collections.Counter)
    for n, r in enumerate(log, 2):
        e = []
        if r["work_key"] not in idx: e.append("work_key not in works_index")
        elif r["record_id"] not in found.get(r["work_key"], ()): e.append("record_id not found in the work")
        if r["ref_id"] not in refs: e.append(f"unknown ref_id {r['ref_id']}")
        if r["status"] not in STATUS: e.append(f"bad status {r['status']}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"] or ""): e.append("date not YYYY-MM-DD")
        if r["status"] == "corrected" and not r["corrected_text"].strip(): e.append("corrected without corrected_text")
        if e: errors.append(f"line {n}: {r['record_id']}: " + "; ".join(e))
        else: summ[r["work_key"]][r["status"]] += 1
    scored = {}
    q = os.path.join(repo, "reports/ocr_quality_works.tsv")
    if os.path.exists(q): scored = {r["work"]: r["records_scored"] for r in rd("reports/ocr_quality_works.tsv")}
    os.makedirs(os.path.join(repo, "reports"), exist_ok=True)
    with open(os.path.join(repo, "reports/verification_summary.tsv"), "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["work", "ocr_records_scored", *sorted(STATUS), "total_checked"])
        for wk in sorted(set(summ) | set(scored)):
            c = summ.get(wk, collections.Counter())
            w.writerow([wk, scored.get(wk, ""), *[c[s] for s in sorted(STATUS)], sum(c.values())])
    print(f"verification log: {len(log)} rows, {len(errors)} errors")
    for e in errors: print("  ", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); main(ap.parse_args().repo)
