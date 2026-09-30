#!/usr/bin/env python3
"""
ingest_archive_works.py - v27: works found only as archive.org scans, for any collection. Never retyped.
(Generalises ingest_nur_archive.py, v20: the target folder comes from the catalog.)

Complements ingest_nur_canon.py (OpenITI). These works are not in OpenITI, so the text is
archive.org's own OCR (tesseract) of a scanned edition: source_type = ocr_uncorrected.
Same OCR method as ingest_misc.py (v10): one row per scanned leaf, from the item's
_hocr_searchtext.txt.gz + _hocr_pageindex.json.gz, with the printed page number archive.org
detected (_page_numbers.json).

catalogs/archive_works.tsv      folder, key, item, file base, work, scholar, role, note, and the md5 of each of
                                the three archive.org files (the build refuses any file whose md5 differs)
Output per work:
  corpus/<folder>/<work>.jsonl.gz   one row per leaf: id, work, leaf, printed_page, text_raw, text, provenance
  sources/archive/<folder>/<work>/   the three archive.org files, byte-exact
  catalogs/archive_works_manifest.json   rows for works_index.tsv (keys <folder>.<work>)

Usage:  python3 pipeline/works/ingest_archive_works.py --repo . --build
"""
import argparse, csv, gzip, hashlib, json, os, re, time, urllib.parse, urllib.request

SUFFIX = {"text": "_hocr_searchtext.txt.gz", "index": "_hocr_pageindex.json.gz", "pages": "_page_numbers.json"}


def fetch(item, name, md5):
    url = f"https://archive.org/download/{item}/{urllib.parse.quote(name)}"
    for attempt in range(5):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "islamic-library"}), timeout=300).read()
            if hashlib.md5(raw).hexdigest() != md5:
                raise SystemExit(f"md5 mismatch for {item}/{name}: archive.org file changed, re-pin before building")
            return raw
        except SystemExit:
            raise
        except Exception as e:
            print("retry", item, name, e, flush=True); time.sleep(5 * (attempt + 1))
    raise SystemExit(f"could not download {item}/{name}")


def build(repo):
    cat = list(csv.DictReader(open(os.path.join(repo, "catalogs/archive_works.tsv"), encoding="utf-8"), delimiter="\t"))
    manifest = []
    for c in cat:
        work = c["key"]; fo = c["folder"]; src = os.path.join(repo, "sources/archive", fo, work); os.makedirs(src, exist_ok=True)
        os.makedirs(os.path.join(repo, "corpus", fo), exist_ok=True)
        raw = {}
        for role, suf in SUFFIX.items():
            name = c["file_base"] + suf
            raw[role] = fetch(c["item"], name, c[f"md5_{role}"])
            open(os.path.join(src, re.sub(r"[^\w.-]", "_", role + suf)), "wb").write(raw[role])
        text = gzip.decompress(raw["text"]).decode("utf-8")
        index = json.loads(gzip.decompress(raw["index"]))
        pages = {p["leafNum"]: p.get("pageNumber") for p in json.loads(raw["pages"])["pages"]}
        out = os.path.join(repo, "corpus", fo, work + ".jsonl.gz"); n = 0
        with gzip.GzipFile(out, "wb", mtime=0) as gz:
            for leaf, (s0, e0, *_rest) in enumerate(index, 1):
                t = text[s0:e0]; n += 1
                r = {"id": f"urn:lib:{fo}.{work}:{n:05d}", "work": c["work"], "leaf": leaf,
                     "printed_page": pages.get(leaf) or None, "text_raw": t, "text": re.sub(r"\s+", " ", t).strip(),
                     "provenance": {"source": "archive.org", "items": [c["item"]], "file": c["file_base"],
                                    "method": "imported", "source_type": "ocr_uncorrected", "status": "unverified"}}
                gz.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))
        manifest.append({"key": f"{fo}.{work}", "work": f"{c['scholar']}: {c['work']}", "author": fo,
                         "strand": c["strand"], "scholar": c["scholar"], "role": c["role"],
                         "attribution": "secure", "category": "primary", "source_type": "ocr_uncorrected",
                         "note": f"{fo} (archive.org), {c['strand']} ({c['role']}); item {c['item']}" + (f"; {c['note']}" if c["note"] else "")})
        print(fo, work, n, "leaves", flush=True)
    json.dump(manifest, open(os.path.join(repo, "catalogs/archive_works_manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.build: build(a.repo)
    else: ap.print_help()
