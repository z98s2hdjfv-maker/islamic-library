#!/usr/bin/env python3
"""
edition_numbers.py - v37: the printed edition numbers for hadith whose layer number differs from the one people cite.

The hadith layer (apparatus/hadith) numbers al-Tirmidhi sequentially and al-Bukhari by al-Bugha's edition (7,124),
while most books and websites cite al-Tirmidhi by the Shakir / ʿAbd al-Baqi numbers (3,956) and al-Bukhari by the
Fath al-Bari numbers (7,563). This adds those numbers beside the layer's own, so a hadith can be cited as people
will look it up. The layer's number and id never change.

  al-Tirmidhi  exact: the layer's own text (0279Tirmidhi.Sunan.JK000140-ara1) prints each hadith's number as a
               heading ("### ||| 2139") just before it; the build of v16 did not read these.
  al-Bukhari   by text: OpenITI 0256Bukhari.Sahih.Shamela0001681-ara1 prints the Fath al-Bari number before each
               hadith ("### | 2067 -"); each layer hadith is matched to it by shared 5-word sequences, accepted when
               at least half of the layer hadith's sequences match (column match), as for al-Dhahabi (v35).
Output
  apparatus/hadith_numbers/<collection>.tsv   hadith_id, layer_number, edition_number, edition, method, match
  apparatus/hadith/<collection>.jsonl.gz      each record gains "edition_numbers": [{"number", "edition"}]
Pins: catalogs/edition_numbers_pins.json (--pin writes it; the build refuses a file that differs).
Usage: python3 pipeline/hadith/edition_numbers.py --repo . [--pin --meta OpenITI_Github_clone_metadata_light.csv]
"""
import argparse, collections, csv, gzip, hashlib, io, json, os, re, subprocess, sys, urllib.request

EDITIONS = {"0279Tirmidhi.Sunan": "Shakir / ʿAbd al-Baqi numbering", "0256Bukhari.Sahih": "Fath al-Bari numbering"}
BUKHARI_FATH = "0256Bukhari.Sahih.Shamela0001681-ara1"


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "islamic-library"}), timeout=300).read()


def pin(repo, meta):
    v = next(r for r in csv.DictReader(open(meta, encoding="utf-8"), delimiter="\t") if r["versionUri"] == BUKHARI_FATH)
    m = re.match(r"https://raw.githubusercontent.com/OpenITI/([^/]+)/[^/]+/(.+)$", v["url"])
    rp, path = m.group(1), m.group(2)
    commit = subprocess.check_output(["git", "ls-remote", f"https://github.com/OpenITI/{rp}.git", "HEAD"], text=True).split()[0]
    raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{rp}/{commit}/{path}")
    json.dump({BUKHARI_FATH: {"repo": rp, "commit": commit, "path": path, "sha256": hashlib.sha256(raw).hexdigest()}},
              open(os.path.join(repo, "catalogs/edition_numbers_pins.json"), "w"), indent=1)


def gz_lines(p):
    return [json.loads(l) for l in gzip.open(p, "rt", encoding="utf-8")]


def tirmidhi(repo, layer):
    by_unit = {h["source_ids"][0]: h for h in layer if h.get("source_ids")}
    cur, out = None, {}
    for r in gz_lines(os.path.join(repo, "corpus/hadith/0279Tirmidhi.Sunan.jsonl.gz")):
        if r.get("kind") == "heading":
            m = re.fullmatch(r"#+\s*\|+\s*(\d+)\s*", r.get("text_raw", ""))
            if m: cur = int(m.group(1))
            continue
        if r["id"] in by_unit and cur is not None:
            out[by_unit[r["id"]]["id"]] = (cur, "heading in the layer's own text", ""); cur = None
    return out


def bukhari(repo, layer):
    sys.path.insert(0, os.path.join(repo, "pipeline/search")); from textnorm import norm
    W = re.compile(r"[ء-ي]{2,}")
    p = json.load(open(os.path.join(repo, "catalogs/edition_numbers_pins.json")))[BUKHARI_FATH]
    raw = fetch(f"https://raw.githubusercontent.com/OpenITI/{p['repo']}/{p['commit']}/{p['path']}")
    if hashlib.sha256(raw).hexdigest() != p["sha256"]: sys.exit("sha256 mismatch for " + BUKHARI_FATH)
    t = raw.decode("utf-8").split("#META#Header#End#", 1)[-1]
    parts = re.split(r"### \|+ (\d{1,4}) -", t)          # [pre, n1, text1, n2, text2, ...]
    idx = collections.defaultdict(set)
    for k in range(1, len(parts) - 1, 2):
        n = int(parts[k]); ws = W.findall(norm(re.sub(r"PageV\d+P\d+|~~|#", " ", parts[k + 1])))[:80]
        for i in range(len(ws) - 4): idx[" ".join(ws[i:i + 5])].add(n)
    units = {r["id"]: r.get("text", "") for r in gz_lines(os.path.join(repo, "corpus/hadith/0256Bukhari.Sahih.jsonl.gz"))}
    out = {}
    for h in layer:
        ws = W.findall(norm(" ".join(units.get(u, "") for u in h.get("source_ids", []))))[:80]
        v = collections.Counter()
        for i in range(len(ws) - 4):
            for n in idx.get(" ".join(ws[i:i + 5]), ()): v[n] += 1
        if not v: continue
        n, sc = v.most_common(1)[0]; share = sc / max(1, len(ws) - 4)
        if share >= .5: out[h["id"]] = (n, f"text match to {BUKHARI_FATH}", round(share, 2))
    return out


def main(repo):
    for col, fn in (("0279Tirmidhi.Sunan", tirmidhi), ("0256Bukhari.Sahih", bukhari)):
        lp = os.path.join(repo, f"apparatus/hadith/{col}.jsonl.gz")
        layer = gz_lines(lp); mp = fn(repo, layer)
        os.makedirs(os.path.join(repo, "apparatus/hadith_numbers"), exist_ok=True)
        with open(os.path.join(repo, f"apparatus/hadith_numbers/{col}.tsv"), "w", encoding="utf-8") as f:
            c = csv.writer(f, delimiter="\t", lineterminator="\n")
            c.writerow(["hadith_id", "layer_number", "edition_number", "edition", "method", "match", "uncertain"])
            seq = [h["id"] for h in layer if h["id"] in mp]; cnt = collections.Counter(mp[k][0] for k in seq); unc = {}
            for i, k in enumerate(seq):   # a number claimed twice, or out of order with both neighbours, is flagged
                n = mp[k][0]; prv = mp[seq[i - 1]][0] if i else None; nxt = mp[seq[i + 1]][0] if i + 1 < len(seq) else None
                why = (["shared number"] if cnt[n] > 1 else []) + \
                      (["out of order"] if prv is not None and nxt is not None and not (prv <= n <= nxt) and prv <= nxt else [])
                if why: unc[k] = ", ".join(why)
            for h in layer:
                if h["id"] in mp:
                    n, how, sc = mp[h["id"]]; c.writerow([h["id"], h["number"], n, EDITIONS[col], how, sc, unc.get(h["id"], "")])
        with open(lp, "wb") as fz, gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="") as gz, \
             io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as fo:
            for h in layer:
                h.pop("edition_numbers", None)
                if h["id"] in mp:
                    h["edition_numbers"] = [{"number": mp[h["id"]][0], "edition": EDITIONS[col], **({"uncertain": unc[h["id"]]} if h["id"] in unc else {})}]
                fo.write(json.dumps(h, ensure_ascii=False) + "\n")
        print(f"{col}: {len(mp)} of {len(layer)} hadith numbered ({EDITIONS[col]}); flagged uncertain: {len(unc)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--pin", action="store_true"); ap.add_argument("--meta")
    a = ap.parse_args(); repo = os.path.abspath(a.repo)
    if a.pin: pin(repo, a.meta)
    else: main(repo)
