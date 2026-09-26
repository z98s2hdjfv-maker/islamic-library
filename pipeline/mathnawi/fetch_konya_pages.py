#!/usr/bin/env python3
"""
fetch_konya_pages.py — regenerate Konya 677 AH page images from Ganjoor.

Source: Ganjoor museum artifact `masnavi-konya-677` (687 pages, scan of the
1993 Turkish facsimile). Original-resolution files are served at
  https://i.ganjoor.net/images/masnavi-konya-677/orig/NNNN.jpg
and are byte-identical to the images in the v2-konya release packs
(verified 2026-09-26 on page 0021 and all of parts 00, 03-06).

Usage: fetch_konya_pages.py OUTDIR [first last]   (default 1 687)
Checks every file against the size Ganjoor's API reports.
"""
import json, os, sys, urllib.request
API = 'https://api.ganjoor.net/api/artifacts/masnavi-konya-677'
IMG = 'https://i.ganjoor.net/images/masnavi-konya-677/orig/{}'

def main():
    out = sys.argv[1]; lo, hi = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1, 687)
    os.makedirs(out, exist_ok=True)
    items = json.load(urllib.request.urlopen(API, timeout=120))['items']
    bad = []
    for it in items:
        im = it['images'][0]; fn = im['originalFileName']; n = int(fn[:4])
        if not lo <= n <= hi: continue
        p = os.path.join(out, fn)
        if not (os.path.exists(p) and os.path.getsize(p) == im['fileSizeInBytes']):
            urllib.request.urlretrieve(IMG.format(fn), p)
        if os.path.getsize(p) != im['fileSizeInBytes']: bad.append(fn)
    print('size mismatches:', bad or 'none')

if __name__ == '__main__':
    main()
