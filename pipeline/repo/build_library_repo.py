#!/usr/bin/env python3
"""
build_library_repo.py — assemble the Islamic library repo from working files.

Layers (data flows one way, never edited upstream):
  sources/ -> corpus/ -> apparatus/ -> annotations/
  plus catalogs/, pipeline/, reports/, docs/
Large binaries (scans, image packs) go to release_assets/, which is NOT
committed; upload those files as GitHub Release assets instead.

Usage:
  python3 build_library_repo.py --src /mnt/project --out ./islamic-library
  python3 build_library_repo.py --src DIR --master mathnawi_library_v6.zip \
      [--images konya_pages_part01.zip ...] --out ./islamic-library --zip

Nothing in --src is modified. Every placed file is recorded in MANIFEST.tsv
with its SHA-256 and original name, so any file can be traced to its origin.
"""
import argparse, hashlib, os, re, shutil, subprocess, sys, zipfile, tempfile
from datetime import date

LAYERS = ["sources", "corpus", "apparatus", "annotations", "catalogs",
          "pipeline", "reports", "docs"]

# (regex on original filename, destination dir, rename function or None)
# First match wins. Order matters: specific rules before general ones.
RULES = [
    # --- Mathnawi corpus: full text, one couplet per row
    (r"^mathnawi_mathnawi_book(\d)\.tsv$", "corpus/mathnawi",
     lambda m: f"book{m.group(1)}.tsv"),
    (r"^(mathnawi_)?book(\d)\.tsv$", "corpus/mathnawi",
     lambda m: f"book{m.group(2)}.tsv"),
    (r"\.jsonl$", "corpus/mathnawi/jsonl", None),
    # --- Apparatus: witnesses compared, never altering corpus
    (r"^mathnawi_collation_pilot\.tsv$", "apparatus/mathnawi",
     lambda m: "collation_pilot.tsv"),
    (r"^mathnawi_konya_book1_differences\.tsv$", "apparatus/mathnawi/konya",
     lambda m: "book1_differences.tsv"),
    (r"^mathnawi_book1_variants_konya_not_ganjoor\.tsv$",
     "apparatus/mathnawi/konya", lambda m: "book1_variants_konya_not_ganjoor.tsv"),
    (r"^mathnawi_books2-6_konya_not_ganjoor\.tsv$", "apparatus/mathnawi/konya",
     lambda m: "books2-6_konya_not_ganjoor.tsv"),
    (r"(collation|witness|variant|konya).*\.(tsv|txt|json)$",
     "apparatus/mathnawi", None),
    # --- Annotations: interpretive layer, keyed to verse IDs
    (r"^mathnawi_frames_(.+)\.json$", "annotations/mathnawi/frames",
     lambda m: f"{m.group(1)}.json"),
    (r"^mathnawi_pilot_hadith_check\.json$", "annotations/mathnawi",
     lambda m: "hadith_check_pilot.json"),
    # --- Pipeline: scripts that regenerate everything above
    (r"^mathnawi_(.+)\.py$", "pipeline/mathnawi", lambda m: f"{m.group(1)}.py"),
    (r"^works_(.+)\.py$", "pipeline/works", lambda m: f"{m.group(1)}.py"),
    # --- Reports: outputs of pipeline runs
    (r"^mathnawi_(pilot_report|batch\d+_report|mathnawi_summary|mathnawi_warnings)\.json$",
     "reports/mathnawi",
     lambda m: m.group(1).replace("mathnawi_", "") + ".json"),
    # --- Catalogs: what exists and where it came from
    (r"^works_(.+)\.(json|md)$", "catalogs",
     lambda m: f"{m.group(1)}.{m.group(2)}"),
    # --- Docs
    (r"^mathnawi_(README|SPEC_STATUS)\.md$", "docs/mathnawi",
     lambda m: f"{m.group(1)}.md"),
    # --- Provenance files
    (r"^SHA256SUMS", "sources", None),
    # --- Large binaries: never committed, published as release assets
    (r"\.(pdf|zip|png|jpe?g|tiff?)$", "release_assets", None),
]

LARGE_BYTES = 50 * 1024 * 1024  # GitHub warns at 50 MB, rejects at 100 MB


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def route(name):
    for pat, dest, rename in RULES:
        m = re.search(pat, name, re.IGNORECASE)
        if m:
            return dest, (rename(m) if rename else name)
    return "_unsorted", name


def place(src_path, origin_label, out, manifest, seen):
    name = os.path.basename(src_path)
    dest_dir, new_name = route(name)
    if name.lower().endswith(".pdf"):
        with open(src_path, "rb") as fh:
            if fh.read(5) != b"%PDF-":  # e.g. a text dump saved as .pdf
                dest_dir, new_name = "sources", name[:-4] + "_text_dump.txt"
    if os.path.getsize(src_path) > LARGE_BYTES and dest_dir != "release_assets":
        dest_dir = "release_assets"
        new_name = name
    rel = f"{dest_dir}/{new_name}"
    if rel in seen:  # don't silently overwrite: keep both, flag it
        stem, ext = os.path.splitext(new_name)
        rel = f"{dest_dir}/{stem}__from_{origin_label}{ext}"
    seen.add(rel)
    target = os.path.join(out, rel)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copy(src_path, target)  # fresh mtime; source may predate 1980
    manifest.append((rel, sha256(target), os.path.getsize(target),
                     origin_label, name))


def collect(dirpath):
    for root, _, files in os.walk(dirpath):
        for f in sorted(files):
            if not f.startswith("."):
                yield os.path.join(root, f)


README = """# Islamic Library — working repository

Layered corpus for the *Understanding the Quran* project. Data flows one
way; no layer edits the one before it.

| Layer | Holds | Rule |
|---|---|---|
| `sources/` | raw downloads + checksums | never edited |
| `corpus/` | canonical texts (one couplet/verse per row) | byte-exact from source |
| `apparatus/` | variants, collations between witnesses | never alters corpus |
| `annotations/` | frames, hadith checks, scholarly perspectives | keyed to verse IDs |
| `catalogs/` | what works exist and where they came from | |
| `pipeline/` | scripts that regenerate the above | |
| `reports/` | outputs and warnings from pipeline runs | |
| `docs/` | README / spec status per corpus | |

Verse IDs follow `urn:sufi:rumi.mathnawi:<book>.b<nicholson>` (anchored) or
`...g<ganjoor_seq>` (Ganjoor-based). See `docs/mathnawi/README.md`.

Large binaries (scans, page-image packs) are **not** committed. They are
published as GitHub Release assets; see `release_assets.txt`.

`MANIFEST.tsv` lists every file with SHA-256 and original filename.
Built {today}.
"""

GITATTRIBUTES = """*.tsv  text eol=lf diff
*.jsonl text eol=lf
*.md   text eol=lf
*.py   text eol=lf
"""

GITIGNORE = """release_assets/
_unsorted/
__pycache__/
.DS_Store
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder of working files")
    ap.add_argument("--master", help="master zip (e.g. mathnawi_library_*_v6.zip)")
    ap.add_argument("--images", nargs="*", default=[], help="image-pack zips")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zip", action="store_true", help="also zip the repo")
    ap.add_argument("--no-git", action="store_true")
    a = ap.parse_args()

    if os.path.exists(a.out):
        sys.exit(f"{a.out} already exists; remove it or choose another --out")
    for d in LAYERS:
        os.makedirs(os.path.join(a.out, d), exist_ok=True)

    manifest, seen = [], set()

    # Master zip first, so its authoritative copies take the canonical names
    if a.master:
        with tempfile.TemporaryDirectory() as tmp:
            zipfile.ZipFile(a.master).extractall(tmp)
            for p in collect(tmp):
                place(p, "master", a.out, manifest, seen)
    for p in collect(a.src):
        rel_dest, new = route(os.path.basename(p))
        if f"{rel_dest}/{new}" in seen:
            # same file already came from master: verify, don't duplicate
            existing = os.path.join(a.out, rel_dest, new)
            if sha256(existing) == sha256(p):
                continue
        place(p, "project", a.out, manifest, seen)
    for z in a.images:  # keep packs whole, as release assets
        place(z, "images", a.out, manifest, seen)

    # Empty layers get a note so git keeps them and people know their purpose
    notes = {"sources": "Raw downloads land here, untouched, with SHA256SUMS.\n"
             "Ganjoor pin: ganjoor-data @ a64968e7 (poets/moulavi/masnavi).\n"}
    for d in LAYERS:
        path = os.path.join(a.out, d)
        if not os.listdir(path):
            with open(os.path.join(path, "README.md"), "w") as f:
                f.write(notes.get(d, f"`{d}/` layer — see top-level README.\n"))

    with open(os.path.join(a.out, "README.md"), "w") as f:
        f.write(README.format(today=date.today().isoformat()))
    with open(os.path.join(a.out, ".gitattributes"), "w") as f:
        f.write(GITATTRIBUTES)
    with open(os.path.join(a.out, ".gitignore"), "w") as f:
        f.write(GITIGNORE)

    manifest.sort()
    with open(os.path.join(a.out, "MANIFEST.tsv"), "w") as f:
        f.write("path\tsha256\tbytes\torigin\toriginal_name\n")
        for row in manifest:
            f.write("\t".join(map(str, row)) + "\n")

    assets = [r for r in manifest if r[0].startswith("release_assets/")]
    with open(os.path.join(a.out, "release_assets.txt"), "w") as f:
        f.write("# Upload these as GitHub Release assets (not committed)\n")
        for r in assets:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")

    unsorted = [r for r in manifest if r[0].startswith("_unsorted/")]

    if not a.no_git:
        run = lambda *c: subprocess.run(c, cwd=a.out, check=True,
                                        capture_output=True)
        try:
            run("git", "init", "-b", "main")
            run("git", "add", "-A")
            run("git", "-c", "user.name=library-builder",
                "-c", "user.email=builder@localhost",
                "commit", "-m", "Initial layered library structure")
        except Exception as e:
            print(f"git step skipped: {e}")

    if a.zip:
        zpath = a.out.rstrip("/") + ".zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED,
                             strict_timestamps=False) as zf:
            for root, _, files in os.walk(a.out):  # everything, incl. .git
              for fn in files:
                p = os.path.join(root, fn)
                zf.write(p, os.path.relpath(p, os.path.dirname(os.path.abspath(a.out))))

    # Summary
    by_layer = {}
    for r in manifest:
        top = r[0].split("/")[0]
        by_layer.setdefault(top, [0, 0])
        by_layer[top][0] += 1
        by_layer[top][1] += r[2]
    print("Placed files by layer:")
    for k in sorted(by_layer):
        n, b = by_layer[k]
        print(f"  {k:<15} {n:>3} files  {b/1024:>9.1f} KB")
    if unsorted:
        print("\nUNSORTED — add a rule for these:")
        for r in unsorted:
            print("  ", r[4])
    print(f"\nRelease assets to upload separately: {len(assets)}")


if __name__ == "__main__":
    main()
