#!/usr/bin/env python3
"""
add_v6_v7.py - add the v6 Rumi circle and v7 Persian addendum to islamic-library.

Run from the root of a fresh clone of the repo:
    git clone https://github.com/z98s2hdjfv-maker/islamic-library.git
    cd islamic-library
    python3 add_v6_v7.py
    git add -A && git commit -m "Add v6 Rumi circle and v7 Persian addendum" && git push

Downloads both zips from release snapshots-2026-09, checks SHA-256 of the zips
and every file inside, places 115 files, updates MANIFEST.tsv,
works_index.tsv, CORPUS_LOCATIONS.md and pipeline/repo/add_works_batch.py.
Needs only Python 3.9+ (no extra packages). Writes nothing if a check fails.
"""
import hashlib, os, shutil, sys, tempfile, urllib.request, zipfile

REL = "https://github.com/z98s2hdjfv-maker/islamic-library/releases/download/snapshots-2026-09/"
ZIPS = {
  "v6": ("mathnawi_library_2026-09-25_v6_rebuilt.zip", "02e83ae0c3c763d0ffc9f37eaa62561c91d4d5b90ac7469f32ca4aab6857135a"),
  "v7": ("library_v7_addendum_2026-09-25.zip", "ef8ad1a8c068158f9fa89908d402effe14955123b72a00f4ba995f359e2899e8"),
}
ADD_WORKS_BATCH = "#!/usr/bin/env python3\n\"\"\"\nadd_works_batch.py — add an Arabic works batch (Shamela / archive.org / typed)\ninto the layered repo.\n\n  jsonl/<author>.<work>.jsonl -> corpus/<author>/<work>.jsonl\n  bok/*.bok                   -> sources/shamela/\n  src/* (txt, docx, ocr gz)   -> sources/typed/ or sources/ocr/\n  manifests, catalogs         -> catalogs/  (skipped if identical copy exists)\n  SHA256SUMS                  -> sources/checksums/<batch>_SHA256SUMS\n  ingest scripts              -> pipeline/works/ (skipped if identical)\n\nRefuses to run if the batch's own SHA256SUMS does not verify. Appends every\nplaced file to MANIFEST.tsv and rebuilds catalogs/works_index.tsv from all\nmanifests (attribution, category, source type), so agents can see which\ntexts are secure, doubtful or spurious before quoting them.\n\nUsage: add_works_batch.py --batch v9 --dir <unzipped batch> --repo <repo>\n\"\"\"\nimport argparse, hashlib, json, os, shutil, sys, csv, glob\n\ndef sha(p):\n    h = hashlib.sha256()\n    with open(p, 'rb') as f:\n        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)\n    return h.hexdigest()\n\ndef verify(d):\n    ok = True\n    for line in open(os.path.join(d, 'SHA256SUMS'), encoding='utf-8'):\n        if not line.strip(): continue\n        h, p = line.rstrip('\\n').split(None, 1)\n        p = os.path.join(d, p.lstrip('*').removeprefix('./'))\n        if not os.path.exists(p) or sha(p) != h:\n            print('CHECKSUM FAIL', p); ok = False\n    return ok\n\ndef main():\n    a = argparse.ArgumentParser()\n    a.add_argument('--batch', required=True); a.add_argument('--dir', required=True)\n    a.add_argument('--repo', required=True); o = a.parse_args()\n    if not verify(o.dir): sys.exit('batch checksums failed; nothing written')\n    repo_hashes = {}\n    for p in glob.glob(os.path.join(o.repo, '**', '*'), recursive=True):\n        if os.path.isfile(p) and '/.git/' not in p: repo_hashes.setdefault(sha(p), p)\n    placed = []\n    def put(src, rel):\n        h = sha(src)\n        if h in repo_hashes:\n            print('skip (already in repo):', os.path.relpath(repo_hashes[h], o.repo)); return\n        dst = os.path.join(o.repo, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)\n        if os.path.exists(dst): sys.exit(f'refusing to overwrite {rel}')\n        shutil.copy(src, dst); repo_hashes[h] = dst\n        placed.append((rel, h, os.path.getsize(dst), o.batch, os.path.basename(src)))\n    for f in sorted(os.listdir(o.dir)):\n        p = os.path.join(o.dir, f)\n        if f == 'jsonl':\n            for j in sorted(os.listdir(p)):\n                author, work = j.split('.', 1)\n                put(os.path.join(p, j), f'corpus/{author}/{work}')\n        elif f == 'bok':\n            for b in sorted(os.listdir(p)): put(os.path.join(p, b), f'sources/shamela/{b}')\n        elif f == 'src':\n            for s in sorted(os.listdir(p)):\n                sub = 'ocr' if ('_ocr__' in s) else 'typed'\n                put(os.path.join(p, s), f'sources/{sub}/{s}')\n        elif f == 'SHA256SUMS':\n            put(p, f'sources/checksums/{o.batch}_SHA256SUMS')\n        elif f.endswith('.py'):\n            put(p, f'pipeline/works/{f}')\n        elif f.endswith('.json'):\n            name = f if f.startswith(('manifest', 'shamela', 'misc')) else f\n            put(p, f'catalogs/{o.batch}_{name}' if f.startswith('manifest') else f'catalogs/{name}')\n        else:\n            put(p, f'_unsorted/{f}')\n    with open(os.path.join(o.repo, 'MANIFEST.tsv'), 'a', encoding='utf-8') as m:\n        for r in placed: m.write('\\t'.join(map(str, r)) + '\\n')\n    build_index(o.repo)\n    print(f'placed {len(placed)} files from {o.batch}')\n\ndef build_index(repo):\n    rows = {}\n    for mf in sorted(glob.glob(os.path.join(repo, 'catalogs', '*manifest*.json'))):\n        try: data = json.load(open(mf, encoding='utf-8'))\n        except Exception: continue\n        if not isinstance(data, list): continue\n        for r in data:\n            if not isinstance(r, dict) or 'key' not in r: continue\n            author, work = r['key'].split('.', 1)\n            path = f'corpus/{author}/{work}.jsonl'\n            n = sum(1 for _ in open(os.path.join(repo, path), encoding='utf-8')) \\\n                if os.path.exists(os.path.join(repo, path)) else ''\n            rows[r['key']] = [r['key'], author, r.get('work', ''), r.get('attribution', ''),\n                              r.get('category', ''), r.get('source_type') or 'shamela',\n                              (r.get('note') or '').replace('\\t', ' '), path, n]\n    # Persian works from Ganjoor (v6 Rumi circle, v7 addendum): works_summary*.json\n    for sf in sorted(glob.glob(os.path.join(repo, 'catalogs', 'works_summary*.json'))):\n        try: data = json.load(open(sf, encoding='utf-8'))\n        except Exception: continue\n        if not isinstance(data, dict) or data.get('source') != 'ganjoor-data': continue\n        commit = (data.get('commit') or '')[:8]\n        for key, r in data.get('works', {}).items():\n            author, work = key.split('.', 1)\n            path = f'corpus/{author}/{work}.jsonl'\n            full = os.path.join(repo, path)\n            n = sum(1 for _ in open(full, encoding='utf-8')) if os.path.exists(full) else ''\n            rows[key] = [key, author, r.get('title', ''), r.get('attribution') or 'unreviewed',\n                         'primary', 'ganjoor', f'Persian; ganjoor-data {commit}; {os.path.basename(sf)}',\n                         path, n]\n    with open(os.path.join(repo, 'catalogs', 'works_index.tsv'), 'w', encoding='utf-8') as f:\n        w = csv.writer(f, delimiter='\\t', lineterminator='\\n')\n        w.writerow(['key', 'author', 'work', 'attribution', 'category', 'source_type', 'note', 'corpus_path', 'records'])\n        for k in sorted(rows): w.writerow(rows[k])\n\nif __name__ == '__main__':\n    main()\n"
CORPUS_LOCATIONS = "# Corpus locations — Islamic Library\n\n**Repo (public):** https://github.com/z98s2hdjfv-maker/islamic-library\n**Master copy:** library snapshot zips on Housam's iPad (Mathnawī v1–v6, library v7–v10); off-site copy in release `snapshots-2026-09`.\n\n## How a chat should fetch\n- Single file (no auth): `curl -sLO https://raw.githubusercontent.com/z98s2hdjfv-maker/islamic-library/main/<path>`\n- Whole repo: `git clone --depth 1 https://github.com/z98s2hdjfv-maker/islamic-library.git`\n- Large scans: releases `v1-assets` (Fusus, Futūḥāt) and `v2-konya` (Konya 677 AH, all 687 pages in 7 packs) — see `release_assets.txt` for names, SHA-256 and URLs.\n- Konya images can also be regenerated byte-identically: `pipeline/mathnawi/fetch_konya_pages.py`.\n- Fetch to disk and query with code. Do not paste full corpus files into the conversation.\n- Writing to the repo needs a fine-grained token (this repo only, Contents R/W). Housam supplies it per session; never store it in project files or memory.\n\n## What lives where\n| Path | Contents |\n|---|---|\n| corpus/ibnarabi/, corpus/jilani/, corpus/ghazali/ | Arabic works as JSONL (32 works). Folders group texts by *figure*, not strict authorship: commentaries (Jāmī, Pārsā) and misattributed works (al-Qāshānī's tafsir) sit with the figure they concern. **Check catalogs/works_index.tsv (attribution, category, source_type) before quoting anything.** |\n| corpus/openiti/<author>/ | OpenITI texts (v8): al-Ghazālī 52, al-Jīlānī 7, Ibn ʿArabī 9 versions, as JSONL; raw OpenITI files in sources/openiti/. Attribution and primary version per work in catalogs/openiti_catalog.json |\n| corpus/rumi/, corpus/bahawalad/, corpus/sultanwalad/ | v6 Rumi circle (Ganjoor, Persian JSONL): Dīwān-i Shams (diwan.gh ghazals, .rb quatrains, .tj tarjīʿāt, .ms mustadrakāt), Fīhi mā fīhi, Majālis-i sabʿa, Bahāʾ Walad's Maʿārif (part 1), Sulṭān Walad's Waladnāma |\n| corpus/attar/, sanai/, jami/, iraqi/, shabistari/, awhad/, maybudi/ + ghazali/kimiya.k, jilani/diwan.gh | v7 Persian addendum (Ganjoor). Many ʿAṭṭār titles are spurious_attested; jilani/diwan.gh (Persian) is doubtful and distinct from the Arabic jilani/diwan.jsonl. **works_index.tsv now covers these (source_type = ganjoor).** v6 Rumi-circle rows read `unreviewed` until attribution is set. |\n| corpus/mathnawi/full/book1–6.jsonl | v6 full Mathnawī records (25,637 couplets, Nicholson IDs applied; concordance `aligned_unverified`). See docs/mathnawi/README_v6_rebuild.md |\n| corpus/mathnawi/book1–6.tsv | Mathnawi, one couplet per row, Nicholson-numbered IDs (Ganjoor pin a64968e7) |\n| apparatus/mathnawi/ | collation pilot; konya/ Konya-vs-Ganjoor variants |\n| annotations/mathnawi/ | story frames (lion_hare, merchant_parrot, umar_envoy), hadith check |\n| catalogs/ | works summaries, OpenITI catalog, Shamela manifest, source surveys |\n| pipeline/ | ingest scripts (mathnawi/, works/), repo builder (repo/) |\n| reports/mathnawi/ | pilot/batch reports, summary, warnings, per-book v6 reports |\n| reports/works/ | per-work ingest reports for v6/v7 Ganjoor works |\n| sources/shamela/ | original Shamela .bok files (Access DB) the JSONL was built from |\n| sources/typed/, sources/ocr/ | typed txt/docx uploads; archive.org OCR text + page indexes |\n| sources/checksums/ | each batch's original SHA256SUMS (v6, v7, v9, v10) |\n| sources/fusus/ | raw text dump of Fusus (presentation-form glyphs; needs normalising) |\n| docs/mathnawi/ | README, SPEC_STATUS |\n\n## Release assets (v1-assets)\n- **Fusus al-Ḥikam**, ed. Sayyid Niẓām al-Dīn Aḥmad — 520 pp, typeset; text layer has doubled glyphs (presentation form + base letter), removable deterministically.\n- **al-Futūḥāt al-Makkiyya**, ed. ʿAbd al-ʿAzīz Sulṭān al-Manṣūb — 8,242 pp scan, ABBYY OCR with errors. Image witness only; take digital text from OpenITI.\n\n## Attribution flags (from works_index.tsv)\n- spurious_attested: ibnarabi.tafsir_qashani (by al-Qāshānī), ghazali.mukashafa\n- doubtful: ibnarabi.muhadarat_abrar, jilani.sirrasrar, jilani.diwan\n- mixed collections: ibnarabi.rasail.* \n- about, not by: jilani.qalaid, jilani.sayf\n- ocr_uncorrected: ibnarabi.futuhat.mansub_ocr, ibnarabi.fusus.nizamaldin_ocr (witness only)\n\n## Not in the repo (cannot be regenerated by script)\n- v6 Konya couplet-by-couplet tables (Book One, 4,013 rows), variant_sites_konya.tsv (Books 2–6, 1,211 rows), masnavi.net witness text, Nicholson English column — lost with the original v6; summaries live in apparatus/mathnawi/.\n- Still to source: Maktūbāt, Maqālāt-i Shams, Aflākī.\n"

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def main():
    if not os.path.exists("MANIFEST.tsv") or not os.path.isdir("corpus"):
        sys.exit("Run this from the root of the islamic-library clone.")
    if os.path.exists("corpus/mathnawi/full/book1.jsonl"):
        sys.exit("v6 already present; nothing to do.")
    tmp = tempfile.mkdtemp()
    dirs = {}
    for batch, (name, want) in ZIPS.items():
        zp = os.path.join(tmp, name)
        print("downloading", name); urllib.request.urlretrieve(REL + name, zp)
        if sha(zp) != want: sys.exit("zip checksum mismatch: " + name)
        d = os.path.join(tmp, batch); zipfile.ZipFile(zp).extractall(d)
        for line in open(os.path.join(d, "SHA256SUMS"), encoding="utf-8"):
            if not line.strip(): continue
            h, p = line.rstrip("\n").split(None, 1)
            if sha(os.path.join(d, p.lstrip("*").removeprefix("./"))) != h:
                sys.exit("file checksum mismatch in %s: %s" % (batch, p))
        dirs[batch] = d
    print("all checksums OK")
    have = {}
    for r, _, fs in os.walk("."):
        if ".git" in r.split(os.sep): continue
        for f in fs: have.setdefault(sha(os.path.join(r, f)), os.path.join(r, f))
    placed = []
    def put(src, rel, batch):
        h = sha(src)
        if h in have: return
        if os.path.exists(rel): sys.exit("refusing to overwrite " + rel)
        os.makedirs(os.path.dirname(rel), exist_ok=True); shutil.copy(src, rel); have[h] = rel
        placed.append((rel, h, os.path.getsize(rel), batch, os.path.basename(src)))
    def work(src, batch):
        f = os.path.basename(src)
        if f.endswith("_report.json"): put(src, "reports/works/" + f, batch)
        elif f.endswith(".jsonl"):
            a, rest = f.split(".", 1); put(src, "corpus/%s/%s" % (a, rest), batch)
    v6, v7 = dirs["v6"], dirs["v7"]
    for n in range(1, 7):
        put("%s/mathnawi/full/mathnawi_book%d.jsonl" % (v6, n), "corpus/mathnawi/full/book%d.jsonl" % n, "v6")
        put("%s/mathnawi/reports/mathnawi_book%d_report.json" % (v6, n), "reports/mathnawi/book%d_report.json" % n, "v6")
    put(v6 + "/README_v6_rebuild.md", "docs/mathnawi/README_v6_rebuild.md", "v6")
    put(v6 + "/SHA256SUMS", "sources/checksums/v6_SHA256SUMS", "v6")
    for f in sorted(os.listdir(v6 + "/works/data")): work(v6 + "/works/data/" + f, "v6")
    put(v7 + "/SHA256SUMS", "sources/checksums/v7_SHA256SUMS", "v7")
    for f in sorted(os.listdir(v7)): work(v7 + "/" + f, "v7")
    # updated index builder + locations doc
    p = "pipeline/repo/add_works_batch.py"
    open(p, "w", encoding="utf-8").write(ADD_WORKS_BATCH)
    open("CORPUS_LOCATIONS.md", "w", encoding="utf-8").write(CORPUS_LOCATIONS)
    h, n = sha(p), os.path.getsize(p)
    lines = open("MANIFEST.tsv", encoding="utf-8").read().split("\n")
    lines = ["\t".join([p, h, str(n), "chat", "add_works_batch.py"]) if l.startswith(p + "\t") else l for l in lines]
    text = "\n".join(lines)
    if not text.endswith("\n"): text += "\n"
    text += "".join("\t".join(map(str, r)) + "\n" for r in placed)
    open("MANIFEST.tsv", "w", encoding="utf-8").write(text)
    sys.path.insert(0, "pipeline/repo"); import add_works_batch; add_works_batch.build_index(".")
    shutil.rmtree(tmp)
    print("placed %d files; works_index.tsv rebuilt. Now: git add -A && git commit && git push" % len(placed))
    print("(delete add_v6_v7.py before committing if you don't want it in the repo)")

if __name__ == "__main__":
    main()
