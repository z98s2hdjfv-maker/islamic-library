#!/usr/bin/env python3
"""
ingest_quran_hadith.py - v15: the Quran, the main hadith collections and the main tafsirs, from OpenITI.
Never retyped. Same record format as ingest_madhhab_canon.py / ingest_companions_canon.py, plus:

  * Quran: one record per verse, id urn:quran:<sura>:<aya>, fields sura, aya, text (Tanzil Simple Clean).
    OpenITI prefixes the basmala to verse 1 of suras 2-114 (except 9); it is removed again so 'text' is
    Tanzil's verse text verbatim. With --uthmani, the Tanzil Uthmani text (with diacritics) is fetched from
    tanzil.net, checked (114 suras, 6236 verses) and added as 'text_uthmani'; its sha256 is recorded in
    catalogs/quran_tanzil_uthmani.json. If that fetch fails the build continues without it.
    Tanzil text: CC BY 3.0, (C) Tanzil Project, https://tanzil.net - changing the text is not allowed.

catalogs/quran_hadith_canon.tsv        group, book, author, role, attribution, note, version (optional override)
catalogs/quran_hadith_canon_pins.json  exact OpenITI versions (repo, commit, path, sha256); --build refuses mismatches
Output: corpus/<group>/<book>.jsonl.gz, sources/openiti/<group>/<version>.gz, catalogs/quran_hadith_canon_manifest.json

Usage: --pin --meta OpenITI_Github_clone_metadata_light.csv   |   --build [--uthmani]
"""
import argparse, csv, gzip, hashlib, io, json, os, re, subprocess, sys, time, collections

PAGE = re.compile(r"PageV(\d+)P(\d+)"); MS = re.compile(r"\bms\d+\b")
CANON, PINS, MANI = "catalogs/quran_hadith_canon.tsv", "catalogs/quran_hadith_canon_pins.json", "catalogs/quran_hadith_canon_manifest.json"
BASMALA = "بسم الله الرحمن الرحيم "
TANZIL = "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true"


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
    import urllib.request
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "islamic-library"}), timeout=300).read()
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
        vs = by[c["book"]]
        v = [x for x in vs if x["versionUri"] == c["version"]][0] if c.get("version") else \
            max(vs, key=lambda v: (v["uncorrected_OCR"] != "True", v["status"] == "pri", int(v["tok_length"] or 0)))
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
    json.dump({"source": "OpenITI (github.com/OpenITI)", "license": "CC BY-NC-SA 4.0 (Quran: Tanzil, CC BY 3.0)",
               "pinned": time.strftime("%Y-%m-%d"), "works": pins},
              open(os.path.join(repo, PINS), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def quran_verses(raw):
    body = raw.decode("utf-8").split("#META#Header#End#", 1)[-1].splitlines()
    verses = []; cur = None
    for l in body:
        l = PAGE.sub("", re.sub(r"\s*\bms\d+\b\s*", " ", l)) if l.startswith(("# ", "~~")) else l  # OpenITI milestones
        m = re.match(r"# (\d+)\s*\|\s*(\d+)\s*\| ?(.*)$", l)
        if m:
            if cur: verses.append(cur)
            cur = [int(m.group(1)), int(m.group(2)), [m.group(3)]]
        elif l.startswith("~~") and cur: cur[2].append(l[2:])
    if cur: verses.append(cur)
    out = []
    for s, a, parts in verses:
        t = re.sub(r"\s+", " ", PAGE.sub("", " ".join(parts))).strip()
        if a == 1 and s not in (1, 9) and t.startswith(BASMALA): t = t[len(BASMALA):]
        out.append((s, a, t))
    return out


def uthmani():
    try:
        raw = fetch(TANZIL)
        rows = {}
        for l in raw.decode("utf-8-sig").splitlines():
            if not l.strip() or l.startswith("#"): continue
            s, a, t = l.split("|", 2); rows[(int(s), int(a))] = t
        if len(rows) != 6236 or len({s for s, _ in rows}) != 114: raise ValueError(f"{len(rows)} verses")
        return raw, rows
    except Exception as e:
        print("::warning::Tanzil Uthmani text not added:", e, flush=True); return None, None


def build(repo, want_uthmani):
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
        prov = {"source": "OpenITI", "repo": p["repo"], "commit": p["commit"], "file": p["path"],
                "sha256": p["sha256"], "method": "imported", "status": "unverified"}
        n = 0
        with open(out, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
             io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
            if g == "quran":
                verses = quran_verses(raw)
                if len(verses) != 6236: sys.exit(f"Quran: expected 6236 verses, got {len(verses)}")
                uraw, urows = uthmani() if want_uthmani else (None, None)
                if uraw:
                    usrc = os.path.join(repo, "sources/tanzil/quran-uthmani.txt.gz"); os.makedirs(os.path.dirname(usrc), exist_ok=True)
                    with open(usrc, "wb") as f:
                        with gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z: z.write(uraw)
                    json.dump({"url": TANZIL, "fetched": time.strftime("%Y-%m-%d"), "sha256": hashlib.sha256(uraw).hexdigest(),
                               "bytes": len(uraw), "license": "CC BY 3.0, (C) Tanzil Project, https://tanzil.net"},
                              open(os.path.join(repo, "catalogs/quran_tanzil_uthmani.json"), "w"), indent=1)
                    written.append(usrc)
                for s, a, t in verses:
                    rec = {"id": f"urn:quran:{s}:{a}", "work": c["book"], "version": p["version"], "group": g,
                           "sura": s, "aya": a, "kind": "verse", "text": t}
                    if urows: rec["text_uthmani"] = urows[(s, a)]
                    rec["provenance"] = prov; fo.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
            else:
                for i, q in enumerate(parse(raw.decode("utf-8")), 1):
                    rec = {"id": f"urn:openiti:{p['version']}:p{i:05d}", "work": c["book"], "version": p["version"],
                           "group": g, "author_name": c["author"], "role": c["role"], "kind": q["kind"], "vol": q["vol"], "page_before": q["page"]}
                    if q["kind"] == "heading": rec.update(level=q["level"], text_raw=q["text_raw"])
                    else:
                        rec["text_raw"] = "\n".join(q["lines"]); rec["headings"] = q["heads"]
                        rec["text"] = re.sub(r"\s+", " ", MS.sub("", PAGE.sub("", rec["text_raw"]))).strip()
                    rec["provenance"] = prov; fo.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
        manifest.append({"key": f"{g}.{c['book']}", "work": f"{c['author']}: {c['book'].split('.', 1)[1]}", "author": g,
                         "attribution": c["attribution"], "category": "primary", "source_type": p["source_type"],
                         "note": f"{c['role']}; OpenITI {p['version']}" + (f"; {c['note']}" if c["note"] else "")})
        written += [src, out]
        print(g, c["book"], n, "units", flush=True)
    json.dump(manifest, open(os.path.join(repo, MANI), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(repo, "MANIFEST.tsv"), "a", encoding="utf-8") as m:
        for f in written:
            m.write("\t".join([os.path.relpath(f, repo), hashlib.sha256(open(f, "rb").read()).hexdigest(),
                               str(os.path.getsize(f)), "v15", os.path.basename(f)]) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=".")
    ap.add_argument("--pin", action="store_true"); ap.add_argument("--meta")
    ap.add_argument("--build", action="store_true"); ap.add_argument("--uthmani", action="store_true")
    a = ap.parse_args()
    if a.pin: pin(a.meta, a.repo)
    if a.build: build(a.repo, a.uthmani)
