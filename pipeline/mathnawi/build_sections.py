#!/usr/bin/env python3
"""
build_sections.py - v54: Rumi's own prose headings for the 972 sections of the Mathnawi, with each section's couplets.

The couplet files (corpus/mathnawi/book1..6.tsv) carry a section number but not the heading Rumi wrote over the
section ("The story of the grocer and the parrot, and the parrot's spilling the oil in the shop"). The headings are
his own signposts: they say where a tale begins, where he leaves it to comment, and where he returns to it. This
script reads them from the same pinned Ganjoor commit the text came from and writes one row per section.

Output  apparatus/mathnawi/sections.tsv
  book, section, heading (Persian, as in the source), kind, first_id, last_id, first_nicholson, last_nicholson, couplets
  kind is derived from the heading's first words and is a guide only:
    tale        opens a tale or parable        (حکایت، داستان، قصه، مثل، تمثیل، مثال)
    return      goes back to a tale left off   (رجوع، بقیه، باقی، تتمه، باز گفتن، بازگشتن، تمامی)
    exposition  Rumi comments or explains      (بیان، در بیان، در معنی، تفسیر، شرح، سبب، صفت، حکمت، فرق)
    step        a step in the telling (anything else: "The king sends messengers to Samarqand")
Only the heading (Title) is read. Ganjoor's machine-written summaries of poems and couplets are NOT imported.
Usage: python3 pipeline/mathnawi/build_sections.py --repo . [--cache DIR]     (fetches 972 small files, about a minute)
"""
import argparse, concurrent.futures as cf, csv, hashlib, json, os, re, ssl, urllib.request

COMMIT = "a64968e78425b2e8c7904fbdf5289fba8251a757"
SECTIONS = {1: 172, 2: 115, 3: 228, 4: 139, 5: 178, 6: 140}
URL = "https://raw.githubusercontent.com/ganjoor/ganjoor-data/{c}/poets/moulavi/masnavi/daftar{b}/sh{s}.json"
KIND = [("return", ("رجوع", "بقیهٔ", "بقیه", "باقی", "تتمهٔ", "تتمه", "باز گفتن", "بازگشتن", "تمامی", "باز آمدن به", "مکرر")),
        ("tale", ("حکایت", "داستان", "قصهٔ", "قصه", "مثل", "تمثیل", "مثال", "حکایة")),
        ("exposition", ("بیان", "در بیان", "در معنی", "در تفسیر", "تفسیر", "شرح", "سبب", "صفت", "در صفت", "حکمت", "فرق", "معنی", "هم در بیان", "ذکر"))]


def kind(h):
    for k, starts in KIND:
        if any(h == s or h.startswith(s + " ") for s in starts): return k
    return "step"


def fetch(b, s, cache):
    p = os.path.join(cache, f"d{b}_sh{s}.json") if cache else None
    if p and os.path.exists(p): return open(p, "rb").read()
    ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None)
    d = urllib.request.urlopen(URL.format(c=COMMIT, b=b, s=s), timeout=60, context=ctx).read()
    if p: open(p, "wb").write(d)
    return d


def main(repo, cache):
    if cache: os.makedirs(cache, exist_ok=True)
    jobs = [(b, s) for b, n in SECTIONS.items() for s in range(1, n + 1)]
    with cf.ThreadPoolExecutor(8) as ex: raw = list(ex.map(lambda j: fetch(j[0], j[1], cache), jobs))
    head = {}
    for (b, s), d in zip(jobs, raw):
        t = json.loads(d)["Title"]
        head[(b, s)] = re.sub(r"^بخش\s*[۰-۹0-9]+\s*-\s*", "", t).strip()
    span = {}
    for b in SECTIONS:
        for r in csv.DictReader(open(os.path.join(repo, f"corpus/mathnawi/book{b}.tsv"), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            nic = r.get("nicholson") or r.get("nicholson_derived") or ""
            x = span.setdefault((b, int(r["section"])), {"first": r["id"], "n": 0, "nf": nic})
            x["last"] = r["id"]; x["n"] += 1
            if nic: x["nl"] = nic; x["nf"] = x["nf"] or nic
    out = os.path.join(repo, "apparatus/mathnawi/sections.tsv")
    with open(out, "w", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["book", "section", "heading", "kind", "first_id", "last_id", "first_nicholson", "last_nicholson", "couplets"])
        for (b, s) in jobs:
            x = span.get((b, s))
            if not x: raise SystemExit(f"book {b} section {s}: no couplets in the corpus")
            w.writerow([b, s, head[(b, s)], kind(head[(b, s)]), x["first"], x["last"], x.get("nf", ""), x.get("nl", ""), x["n"]])
    sha = hashlib.sha256("\n".join(head[j] for j in jobs).encode("utf-8")).hexdigest()
    json.dump({"source": "ganjoor-data", "commit": COMMIT, "folder": "poets/moulavi/masnavi/daftar1-6", "field": "Title",
               "sections": len(jobs), "headings_sha256": sha, "note": "machine-written summaries in the source are not imported"},
              open(os.path.join(repo, "catalogs/mathnawi_sections_pins.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(jobs)} sections -> apparatus/mathnawi/sections.tsv; headings sha256 {sha[:16]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--cache")
    a = ap.parse_args(); main(os.path.abspath(a.repo), a.cache)
