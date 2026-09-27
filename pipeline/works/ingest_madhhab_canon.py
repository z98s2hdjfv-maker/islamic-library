#!/usr/bin/env python3
"""
ingest_madhhab_canon.py - import the core canon of the four Sunni schools from OpenITI. Never retyped.

catalogs/madhhab_canon.tsv   school, OpenITI book URI, jurist, role, note (58 works, chosen by Claude
                             as the standard canon: founding corpus, usul, mukhtasar, great commentary,
                             legal maxims, relied-on late reference - a scholar should review the list)
catalogs/madhhab_canon_pins.json   the exact OpenITI version per work: repo, commit, path, sha256
                             (written by --pin; the build refuses any file whose sha256 differs)

Version choice: typed over OCR, then OpenITI's own 'pri' version, then the longest.
Output per work (school folder = search 'author', so --author hanafi etc. works):
  corpus/<school>/<book>.jsonl.gz       one row per OpenITI paragraph/heading, same format as v8,
                                        gzip (-n) because the canon is ~1.3 GB uncompressed
  sources/openiti/<school>/<version>.gz raw OpenITI file, gzip (-n, byte-reproducible)
  catalogs/madhhab_canon_manifest.json  key/work/author/attribution/... rows for works_index.tsv
Works already in the repo (al-Ghazali's Mustasfa and Wasit under corpus/openiti/) are not duplicated.

Usage:  --pin   --meta OpenITI_Github_clone_metadata_light.csv   (resolve versions + commits)
        --build                                                  (download pinned files, write corpus)
"""
import argparse, csv, gzip, hashlib, io, json, os, re, subprocess, sys, time, urllib.request, collections

PAGE = re.compile(r"PageV(\d+)P(\d+)"); MS = re.compile(r"\bms\d+\b")
SCHOOL_AR = {"hanafi": "Hanafi", "maliki": "Maliki", "shafii": "Shafi'i", "hanbali": "Hanbali"}


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


def fetch(url, tries=4):
    for k in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=300).read()
        except Exception as e:
            if k == tries - 1: raise
            time.sleep(5 * (k + 1))


def pin(meta_csv, repo_dir):
    canon = list(csv.DictReader(open(os.path.join(repo_dir, "catalogs/madhhab_canon.tsv"), encoding="utf-8"), delimiter="\t"))
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(meta_csv, encoding="utf-8"), delimiter="\t"): by[r["book"]].append(r)
    heads = {}; pins = {}
    for c in canon:
        vs = by[c["book"]]
        v = max(vs, key=lambda v: (v["uncorrected_OCR"] != "True", v["status"] == "pri", int(v["tok_length"] or 0)))
        m = re.match(r"https://raw.githubusercontent.com/OpenITI/([^/]+)/[^/]+/(.+)$", v["url"])
        repo, path = m.group(1), m.group(2)
        if repo not in heads:
            heads[repo] = subprocess.check_output(["git", "ls-remote", f"https://github.com/OpenITI/{repo}.git", "HEAD"], text=True).split()[0]
        url = f"https://raw.githubusercontent.com/OpenITI/{repo}/{heads[repo]}/{path}"
        raw = fetch(url)
        pins[c["book"]] = {"version": v["versionUri"], "repo": repo, "commit": heads[repo], "path": path,
                           "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                           "source_type": "ocr_uncorrected" if v["uncorrected_OCR"] == "True" else "typed",
                           "openiti_status": v["status"], "tok_length": int(v["tok_length"] or 0)}
        print(c["book"], pins[c["book"]]["version"], len(raw), flush=True)
    json.dump({"source": "OpenITI (github.com/OpenITI)", "license": "CC BY-NC-SA 4.0", "pinned": time.strftime("%Y-%m-%d"),
               "works": pins}, open(os.path.join(repo_dir, "catalogs/madhhab_canon_pins.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def build(repo_dir):
    canon = list(csv.DictReader(open(os.path.join(repo_dir, "catalogs/madhhab_canon.tsv"), encoding="utf-8"), delimiter="\t"))
    pins = json.load(open(os.path.join(repo_dir, "catalogs/madhhab_canon_pins.json"), encoding="utf-8"))["works"]
    manifest = []
    for c in canon:
        p = pins[c["book"]]; school = c["school"]
        raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{p['repo']}/{p['commit']}/{p['path']}")
        h = hashlib.sha256(raw).hexdigest()
        if h != p["sha256"]: sys.exit(f"sha256 mismatch for {p['version']}: {h}")
        src = os.path.join(repo_dir, "sources/openiti", school, p["version"] + ".gz")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        with open(src, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as g: g.write(raw)
        paras = parse(raw.decode("utf-8"))
        out = os.path.join(repo_dir, "corpus", school, c["book"] + ".jsonl.gz")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        n = 0
        with open(out, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
             io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
            for i, q in enumerate(paras, 1):
                rec = {"id": f"urn:openiti:{p['version']}:p{i:05d}", "work": c["book"], "version": p["version"],
                       "school": school, "jurist": c["jurist"], "role": c["role"], "kind": q["kind"], "vol": q["vol"], "page_before": q["page"]}
                if q["kind"] == "heading": rec.update(level=q["level"], text_raw=q["text_raw"])
                else:
                    rec["text_raw"] = "\n".join(q["lines"]); rec["headings"] = q["heads"]
                    rec["text"] = re.sub(r"\s+", " ", MS.sub("", PAGE.sub("", rec["text_raw"]))).strip()
                rec["provenance"] = {"source": "OpenITI", "repo": p["repo"], "commit": p["commit"], "file": p["path"],
                                     "sha256": p["sha256"], "method": "imported", "status": "unverified"}
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
        manifest.append({"key": f"{school}.{c['book']}", "work": f"{c['jurist']}: {c['book'].split('.',1)[1]}",
                         "author": school, "school": school, "jurist": c["jurist"], "role": c["role"],
                         "attribution": "secure", "category": "primary", "source_type": p["source_type"],
                         "note": f"{SCHOOL_AR[school]} canon ({c['role']}); OpenITI {p['version']}" + (f"; {c['note']}" if c["note"] else "")})
        print(school, c["book"], n, "units", flush=True)
    json.dump(manifest, open(os.path.join(repo_dir, "catalogs/madhhab_canon_manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    ap.add_argument("--pin", action="store_true"); ap.add_argument("--meta"); ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.pin: pin(a.meta, a.repo)
    if a.build: build(a.repo)
