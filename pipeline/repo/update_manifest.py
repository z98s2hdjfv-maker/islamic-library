#!/usr/bin/env python3
"""
update_manifest.py - v45: keep MANIFEST.tsv true. Every file git tracks (or would track) gets a row
path, sha256, bytes, origin, original_name; rows of files that changed are refreshed, rows of files that are gone
are dropped. Run at the end of every library update (RUN.sh):  python3 pipeline/repo/update_manifest.py --origin v45
"""
import argparse, hashlib, os, subprocess

ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("--origin", required=True)
a = ap.parse_args(); os.chdir(a.repo)
files = [f for f in subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"]).decode().split("\0")
         if f and f != "MANIFEST.tsv" and os.path.isfile(f) and not f.startswith("library-update-")]
head, *lines = open("MANIFEST.tsv", encoding="utf-8").read().rstrip("\n").split("\n")
old = {l.split("\t")[0]: l.split("\t") for l in lines}
out, added, changed = [], 0, 0
for f in sorted(files):
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
    digest, size = h.hexdigest(), str(os.path.getsize(f))
    row = old.get(f)
    if row and row[1] == digest: out.append(row); continue
    added += row is None; changed += row is not None
    out.append([f, digest, size, a.origin, os.path.basename(f)])
with open("MANIFEST.tsv", "w", encoding="utf-8") as fh:
    fh.write(head + "\n" + "".join("\t".join(r) + "\n" for r in out))
print(f"MANIFEST.tsv: {len(out)} files; {added} added, {changed} refreshed, {len(old) - (len(out) - added)} dropped")
