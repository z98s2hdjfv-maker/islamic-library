#!/usr/bin/env python3
"""
ingest_canon.py - v35: one reusable importer for a canon of works from OpenITI and/or archive.org. Never retyped.
Generalises ingest_asma_canon.py (OpenITI) and ingest_archive_works.py (archive.org scans) so a new canon needs
only a catalog, not a new script; unlike ingest_archive_works.py it builds only the canon it is given.

catalogs/<canon>_canon.tsv   one row per work:
  folder   corpus folder (grading, afterlife, modern, tafsir, ...): the key is <folder>.<book>
  layer    classical | modern. Modern works (after c. 1300 AH: al-Albani, Ahmad Shakir, ...) are cited today but are
           not part of the classical tradition; they get category "modern" in works_index.tsv and live in
           corpus/modern/, so they never mix with the classical layer (search: --author modern, or its absence).
  strand, scholar, role, note   what the work is and why it is here
  source   openiti | archive
  book     OpenITI book URI (e.g. 0807NurDinHaythami.MajmacZawaid), or for archive.org <death>Name.Title
  version  optional forced OpenITI version (e.g. the Mustadrak version that carries al-Dhahabi's Talkhis inline)
  item     archive.org item id; file_base: the file bases of its volumes, joined by " || ", in order
catalogs/<canon>_canon_pins.json   exact files: OpenITI repo/commit/path/sha256; archive md5 per file
                                   (written by --pin; the build refuses any file that differs)
Output: corpus/<folder>/<book>.jsonl.gz (OpenITI: one row per paragraph/heading, as v8; archive: one row per
leaf with vol, leaf, printed_page), sources/openiti|archive/<canon>/..., catalogs/<canon>_canon_manifest.json,
and catalogs/works_index.tsv rebuilt from all manifests (pipeline/repo/add_works_batch.py).

Usage:  --canon grading --pin --meta OpenITI_Github_clone_metadata_light.csv
        --canon grading --build
"""
import argparse, csv, gzip, hashlib, io, json, os, re, subprocess, sys, time, urllib.parse, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = re.compile(r"PageV(\d+)P(\d+)"); MS = re.compile(r"\bms\d+\b")
SUFFIX = {"text": "_hocr_searchtext.txt.gz", "index": "_hocr_pageindex.json.gz", "pages": "_page_numbers.json"}


def parse(txt):  # identical to pipeline/works/ingest_openiti.py (v8)
    body = txt.split("#META#Header#End#", 1)[-1].splitlines()
    paras = []; cur = None; vol, page = None, None; heads = []
    def flush():
        nonlocal cur
        if cur: paras.append(cur); cur = None
    for l in body:
        if l.startswith("### |"):
            flush(); lvl = len(re.match(r"### (\|+)", l).group(1)); t = l[4 + lvl:].strip()
            heads = heads[:lvl - 1] + [t]; paras.append({"kind": "heading", "level": lvl, "text_raw": l, "vol": vol, "page": page}); continue
        if l.startswith("# "): flush(); cur = {"kind": "para", "lines": [l[2:]], "vol": vol, "page": page, "heads": list(heads)}
        elif l.startswith("~~") and cur: cur["lines"].append(l[2:])
        elif l.strip():
            flush(); cur = {"kind": "para", "lines": [l], "vol": vol, "page": page, "heads": list(heads)}
        for m in PAGE.finditer(l):
            vol, page = int(m.group(1)), int(m.group(2))
    flush(); return paras


def fetch(url, tries=5):
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "islamic-library"}), timeout=300).read()
        except Exception as e:
            if k == tries - 1: raise
            print("retry", url, e, flush=True); time.sleep(5 * (k + 1))


def gz_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as g: g.write(data)


def rows(repo, canon):
    return list(csv.DictReader(open(os.path.join(repo, f"catalogs/{canon}_canon.tsv"), encoding="utf-8"), delimiter="\t"))


def pin(repo, canon, meta_csv):
    by = collections.defaultdict(list)
    if meta_csv:
        for r in csv.DictReader(open(meta_csv, encoding="utf-8"), delimiter="\t"): by[r["book"]].append(r)
    heads, pins = {}, {}
    for c in rows(repo, canon):
        if c["source"] == "openiti":
            vs = by[c["book"]]
            if not vs: sys.exit(f"not in OpenITI metadata: {c['book']}")
            v = next(v for v in vs if v["versionUri"] == c["version"]) if c.get("version") else \
                max(vs, key=lambda v: (v["uncorrected_OCR"] != "True", v["status"] == "pri", int(v["tok_length"] or 0)))
            m = re.match(r"https://raw.githubusercontent.com/OpenITI/([^/]+)/[^/]+/(.+)$", v["url"])
            rp, path = m.group(1), m.group(2)
            if rp not in heads:
                heads[rp] = subprocess.check_output(["git", "ls-remote", f"https://github.com/OpenITI/{rp}.git", "HEAD"], text=True).split()[0]
            raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{rp}/{heads[rp]}/{path}")
            pins[c["book"]] = {"version": v["versionUri"], "repo": rp, "commit": heads[rp], "path": path,
                               "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                               "source_type": "ocr_uncorrected" if v["uncorrected_OCR"] == "True" else "typed"}
            print(c["book"], v["versionUri"], len(raw), flush=True)
        else:
            md = json.loads(fetch(f"https://archive.org/metadata/{c['item']}"))
            files = {f["name"]: f for f in md["files"]}
            vols = []
            for base in c["file_base"].split(" || "):
                vols.append({"base": base, **{role: files[base + suf]["md5"] for role, suf in SUFFIX.items() if base + suf in files}})
            pins[c["book"]] = {"item": c["item"], "volumes": vols, "source_type": "ocr_uncorrected"}
            print(c["book"], c["item"], len(vols), "volumes", flush=True)
    json.dump({"pinned": time.strftime("%Y-%m-%d"), "works": pins},
              open(os.path.join(repo, f"catalogs/{canon}_canon_pins.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def build(repo, canon, only=None):
    pins = json.load(open(os.path.join(repo, f"catalogs/{canon}_canon_pins.json"), encoding="utf-8"))["works"]
    manifest = []
    for c in rows(repo, canon):
        p = pins[c["book"]]; fo = c["folder"]; modern = c["layer"] == "modern"
        out = os.path.join(repo, "corpus", fo, c["book"] + ".jsonl.gz"); n = 0
        if not only or c["book"] in only:
            recs = []
            if c["source"] == "openiti":
                raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{p['repo']}/{p['commit']}/{p['path']}")
                if hashlib.sha256(raw).hexdigest() != p["sha256"]: sys.exit(f"sha256 mismatch for {p['version']}")
                gz_write(os.path.join(repo, "sources/openiti", canon, p["version"] + ".gz"), raw)
                for i, q in enumerate(parse(raw.decode("utf-8")), 1):
                    rec = {"id": f"urn:openiti:{p['version']}:p{i:05d}", "work": c["book"], "version": p["version"],
                           "strand": c["strand"], "scholar": c["scholar"], "role": c["role"], "layer": c["layer"],
                           "kind": q["kind"], "vol": q["vol"], "page_before": q["page"]}
                    if q["kind"] == "heading": rec.update(level=q["level"], text_raw=q["text_raw"])
                    else:
                        rec["text_raw"] = "\n".join(q["lines"]); rec["headings"] = q["heads"]
                        rec["text"] = re.sub(r"\s+", " ", MS.sub("", PAGE.sub("", rec["text_raw"]))).strip()
                    rec["provenance"] = {"source": "OpenITI", "repo": p["repo"], "commit": p["commit"], "file": p["path"],
                                         "sha256": p["sha256"], "method": "imported", "status": "unverified"}
                    recs.append(rec)
            else:
                for vi, v in enumerate(p["volumes"], 1):
                    raw = {}
                    for role, suf in SUFFIX.items():
                        if role not in v: continue
                        b = fetch(f"https://archive.org/download/{p['item']}/{urllib.parse.quote(v['base'] + suf)}")
                        if hashlib.md5(b).hexdigest() != v[role]: sys.exit(f"md5 mismatch for {p['item']}/{v['base']}{suf}")
                        raw[role] = b
                        open_dir = os.path.join(repo, "sources/archive", canon, c["book"]); os.makedirs(open_dir, exist_ok=True)
                        open(os.path.join(open_dir, re.sub(r"[^\w.-]", "_", v["base"] + suf)), "wb").write(b)
                    text = gzip.decompress(raw["text"]).decode("utf-8"); index = json.loads(gzip.decompress(raw["index"]))
                    pages = {x["leafNum"]: x.get("pageNumber") for x in json.loads(raw["pages"])["pages"]} if "pages" in raw else {}
                    for leaf, (s0, e0, *_r) in enumerate(index, 1):
                        t = text[s0:e0]
                        recs.append({"id": f"urn:lib:{fo}.{c['book']}:v{vi:02d}.{leaf:04d}", "work": c["book"], "vol": vi, "leaf": leaf,
                                     "printed_page": pages.get(leaf) or None, "layer": c["layer"], "text_raw": t,
                                     "text": re.sub(r"\s+", " ", t).strip(),
                                     "provenance": {"source": "archive.org", "items": [p["item"]], "file": v["base"],
                                                    "method": "imported", "source_type": "ocr_uncorrected", "status": "unverified"}})
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
                 io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo_:
                for r in recs: fo_.write(json.dumps(r, ensure_ascii=False) + "\n"); n += 1
            print(fo, c["book"], n, "units", flush=True)
        title = c["book"].split(".", 1)[1] if "." in c["book"] else c["book"]
        manifest.append({"key": f"{fo}.{c['book']}", "work": f"{c['scholar']}: {title}", "author": fo, "strand": c["strand"],
                         "scholar": c["scholar"], "role": c["role"], "layer": c["layer"], "attribution": "secure",
                         "category": "modern" if modern else "primary", "source_type": p["source_type"],
                         "note": f"{canon} canon, {c['strand']} ({c['role']})" + ("; MODERN layer (not classical)" if modern else "") +
                                 (f"; OpenITI {p['version']}" if c["source"] == "openiti" else f"; archive.org {p['item']}") +
                                 (f"; {c['note']}" if c["note"] else "")})
    json.dump(manifest, open(os.path.join(repo, f"catalogs/{canon}_canon_manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.path.insert(0, os.path.join(HERE, "..", "repo")); import add_works_batch
    add_works_batch.build_index(repo)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--canon", required=True)
    ap.add_argument("--pin", action="store_true"); ap.add_argument("--meta"); ap.add_argument("--build", action="store_true")
    ap.add_argument("--only", help="build only these books (comma-separated), for testing; the manifest still lists all")
    a = ap.parse_args()
    if a.pin: pin(a.repo, a.canon, a.meta)
    if a.build: build(a.repo, a.canon, set(a.only.split(",")) if a.only else None)
