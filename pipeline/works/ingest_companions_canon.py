#!/usr/bin/env python3
"""
ingest_companions_canon.py - v14: sources for the Companions, the four caliphs, sira, consensus,
judgeship, isnad criticism, the Sufi bridge, legal/Sufi tafsir, kalam, critics and lexicons,
imported from OpenITI. Never retyped. Same record format as ingest_madhhab_canon.py.

catalogs/companions_canon.tsv        group, OpenITI book URI, author, role, attribution, note
                                     (list drafted by Claude; a scholar should review it)
catalogs/companions_canon_pins.json  exact OpenITI version per work: repo, commit, path, sha256
                                     (written by --pin; --build refuses any file whose sha256 differs)

Output (group folder = search 'author', e.g. --author athar):
  corpus/<group>/<book>.jsonl.gz          one row per OpenITI paragraph/heading, gzip -n
  sources/openiti/<group>/<version>.gz    raw OpenITI file, gzip -n (byte-reproducible)
  catalogs/companions_canon_manifest.json rows picked up by catalogs/works_index.tsv
Attribution comes from the tsv (e.g. Nahj al-balagha = doubtful), not assumed secure.

Usage: --pin --meta OpenITI_Github_clone_metadata_light.csv   |   --build
"""
import argparse, csv, gzip, hashlib, io, json, os, re, subprocess, sys, time, collections

PAGE = re.compile(r"PageV(\d+)P(\d+)"); MS = re.compile(r"\bms\d+\b")
CANON, PINS, MANI = "catalogs/companions_canon.tsv", "catalogs/companions_canon_pins.json", "catalogs/companions_canon_manifest.json"


def parse(txt):  # identical to pipeline/works/ingest_openiti.py (v8) and ingest_madhhab_canon.py
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
    import urllib.request
    for k in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=300).read()
        except Exception:
            if k == tries - 1: raise
            time.sleep(5 * (k + 1))


def canon(repo):
    return list(csv.DictReader(open(os.path.join(repo, CANON), encoding="utf-8"), delimiter="\t"))


def pin(meta_csv, repo):
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(meta_csv, encoding="utf-8"), delimiter="\t"): by[r["book"]].append(r)
    heads = {}; pins = {}
    for c in canon(repo):
        v = max(by[c["book"]], key=lambda v: (v["uncorrected_OCR"] != "True", v["status"] == "pri", int(v["tok_length"] or 0)))
        m = re.match(r"https://raw.githubusercontent.com/OpenITI/([^/]+)/[^/]+/(.+)$", v["url"])
        rp, path = m.group(1), m.group(2)
        if rp not in heads:
            heads[rp] = subprocess.check_output(["git", "ls-remote", f"https://github.com/OpenITI/{rp}.git", "HEAD"], text=True).split()[0]
        raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{rp}/{heads[rp]}/{path}")
        pins[c["book"]] = {"version": v["versionUri"], "repo": rp, "commit": heads[rp], "path": path,
                           "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                           "source_type": "ocr_uncorrected" if v["uncorrected_OCR"] == "True" else "typed",
                           "openiti_status": v["status"], "tok_length": int(v["tok_length"] or 0)}
        print(c["book"], pins[c["book"]]["version"], len(raw), flush=True)
    json.dump({"source": "OpenITI (github.com/OpenITI)", "license": "CC BY-NC-SA 4.0", "pinned": time.strftime("%Y-%m-%d"),
               "works": pins}, open(os.path.join(repo, PINS), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def build(repo):
    pins = json.load(open(os.path.join(repo, PINS), encoding="utf-8"))["works"]
    manifest = []; written = []
    for c in canon(repo):
        p = pins[c["book"]]; g = c["group"]
        raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{p['repo']}/{p['commit']}/{p['path']}")
        h = hashlib.sha256(raw).hexdigest()
        if h != p["sha256"]: sys.exit(f"sha256 mismatch for {p['version']}: {h}")
        src = os.path.join(repo, "sources/openiti", g, p["version"] + ".gz")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        with open(src, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as gz: gz.write(raw)
        out = os.path.join(repo, "corpus", g, c["book"] + ".jsonl.gz")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        n = 0
        with open(out, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
             io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
            for i, q in enumerate(parse(raw.decode("utf-8")), 1):
                rec = {"id": f"urn:openiti:{p['version']}:p{i:05d}", "work": c["book"], "version": p["version"],
                       "group": g, "author_name": c["author"], "role": c["role"], "kind": q["kind"], "vol": q["vol"], "page_before": q["page"]}
                if q["kind"] == "heading": rec.update(level=q["level"], text_raw=q["text_raw"])
                else:
                    rec["text_raw"] = "\n".join(q["lines"]); rec["headings"] = q["heads"]
                    rec["text"] = re.sub(r"\s+", " ", MS.sub("", PAGE.sub("", rec["text_raw"]))).strip()
                rec["provenance"] = {"source": "OpenITI", "repo": p["repo"], "commit": p["commit"], "file": p["path"],
                                     "sha256": p["sha256"], "method": "imported", "status": "unverified"}
                fo.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
        manifest.append({"key": f"{g}.{c['book']}", "work": f"{c['author']}: {c['book'].split('.', 1)[1]}", "author": g,
                         "attribution": c["attribution"], "category": "primary", "source_type": p["source_type"],
                         "note": f"{c['role']}; OpenITI {p['version']}" + (f"; {c['note']}" if c["note"] else "")})
        written += [src, out]
        print(g, c["book"], n, "units", flush=True)
    json.dump(manifest, open(os.path.join(repo, MANI), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(repo, "MANIFEST.tsv"), "a", encoding="utf-8") as m:
        for f in written:
            m.write("\t".join([os.path.relpath(f, repo), hashlib.sha256(open(f, "rb").read()).hexdigest(),
                               str(os.path.getsize(f)), "v14", os.path.basename(f)]) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    ap.add_argument("--pin", action="store_true"); ap.add_argument("--meta"); ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.pin: pin(a.meta, a.repo)
    if a.build: build(a.repo)
