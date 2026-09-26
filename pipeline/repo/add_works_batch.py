#!/usr/bin/env python3
"""
add_works_batch.py — add an Arabic works batch (Shamela / archive.org / typed)
into the layered repo.

  jsonl/<author>.<work>.jsonl -> corpus/<author>/<work>.jsonl
  bok/*.bok                   -> sources/shamela/
  src/* (txt, docx, ocr gz)   -> sources/typed/ or sources/ocr/
  manifests, catalogs         -> catalogs/  (skipped if identical copy exists)
  SHA256SUMS                  -> sources/checksums/<batch>_SHA256SUMS
  ingest scripts              -> pipeline/works/ (skipped if identical)

Refuses to run if the batch's own SHA256SUMS does not verify. Appends every
placed file to MANIFEST.tsv and rebuilds catalogs/works_index.tsv from all
manifests (attribution, category, source type), so agents can see which
texts are secure, doubtful or spurious before quoting them.

Usage: add_works_batch.py --batch v9 --dir <unzipped batch> --repo <repo>
"""
import argparse, hashlib, json, os, shutil, sys, csv, glob

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()

def verify(d):
    ok = True
    for line in open(os.path.join(d, 'SHA256SUMS'), encoding='utf-8'):
        if not line.strip(): continue
        h, p = line.rstrip('\n').split(None, 1)
        p = os.path.join(d, p.lstrip('*').removeprefix('./'))
        if not os.path.exists(p) or sha(p) != h:
            print('CHECKSUM FAIL', p); ok = False
    return ok

def main():
    a = argparse.ArgumentParser()
    a.add_argument('--batch', required=True); a.add_argument('--dir', required=True)
    a.add_argument('--repo', required=True); o = a.parse_args()
    if not verify(o.dir): sys.exit('batch checksums failed; nothing written')
    repo_hashes = {}
    for p in glob.glob(os.path.join(o.repo, '**', '*'), recursive=True):
        if os.path.isfile(p) and '/.git/' not in p: repo_hashes.setdefault(sha(p), p)
    placed = []
    def put(src, rel):
        h = sha(src)
        if h in repo_hashes:
            print('skip (already in repo):', os.path.relpath(repo_hashes[h], o.repo)); return
        dst = os.path.join(o.repo, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst): sys.exit(f'refusing to overwrite {rel}')
        shutil.copy(src, dst); repo_hashes[h] = dst
        placed.append((rel, h, os.path.getsize(dst), o.batch, os.path.basename(src)))
    for f in sorted(os.listdir(o.dir)):
        p = os.path.join(o.dir, f)
        if f == 'jsonl':
            for j in sorted(os.listdir(p)):
                author, work = j.split('.', 1)
                put(os.path.join(p, j), f'corpus/{author}/{work}')
        elif f == 'bok':
            for b in sorted(os.listdir(p)): put(os.path.join(p, b), f'sources/shamela/{b}')
        elif f == 'src':
            for s in sorted(os.listdir(p)):
                sub = 'ocr' if ('_ocr__' in s) else 'typed'
                put(os.path.join(p, s), f'sources/{sub}/{s}')
        elif f == 'SHA256SUMS':
            put(p, f'sources/checksums/{o.batch}_SHA256SUMS')
        elif f.endswith('.py'):
            put(p, f'pipeline/works/{f}')
        elif f.endswith('.json'):
            name = f if f.startswith(('manifest', 'shamela', 'misc')) else f
            put(p, f'catalogs/{o.batch}_{name}' if f.startswith('manifest') else f'catalogs/{name}')
        else:
            put(p, f'_unsorted/{f}')
    with open(os.path.join(o.repo, 'MANIFEST.tsv'), 'a', encoding='utf-8') as m:
        for r in placed: m.write('\t'.join(map(str, r)) + '\n')
    build_index(o.repo)
    print(f'placed {len(placed)} files from {o.batch}')

def build_index(repo):
    rows = {}
    for mf in sorted(glob.glob(os.path.join(repo, 'catalogs', '*manifest*.json'))):
        try: data = json.load(open(mf, encoding='utf-8'))
        except Exception: continue
        if not isinstance(data, list): continue
        for r in data:
            if not isinstance(r, dict) or 'key' not in r: continue
            author, work = r['key'].split('.', 1)
            path = f'corpus/{author}/{work}.jsonl'
            n = sum(1 for _ in open(os.path.join(repo, path), encoding='utf-8')) \
                if os.path.exists(os.path.join(repo, path)) else ''
            rows[r['key']] = [r['key'], author, r.get('work', ''), r.get('attribution', ''),
                              r.get('category', ''), r.get('source_type') or 'shamela',
                              (r.get('note') or '').replace('\t', ' '), path, n]
    # Persian works from Ganjoor (v6 Rumi circle, v7 addendum): works_summary*.json
    for sf in sorted(glob.glob(os.path.join(repo, 'catalogs', 'works_summary*.json'))):
        try: data = json.load(open(sf, encoding='utf-8'))
        except Exception: continue
        if not isinstance(data, dict) or data.get('source') != 'ganjoor-data': continue
        commit = (data.get('commit') or '')[:8]
        for key, r in data.get('works', {}).items():
            author, work = key.split('.', 1)
            path = f'corpus/{author}/{work}.jsonl'
            full = os.path.join(repo, path)
            n = sum(1 for _ in open(full, encoding='utf-8')) if os.path.exists(full) else ''
            rows[key] = [key, author, r.get('title', ''), r.get('attribution') or 'unreviewed',
                         'primary', 'ganjoor', f'Persian; ganjoor-data {commit}; {os.path.basename(sf)}',
                         path, n]
    with open(os.path.join(repo, 'catalogs', 'works_index.tsv'), 'w', encoding='utf-8') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['key', 'author', 'work', 'attribution', 'category', 'source_type', 'note', 'corpus_path', 'records'])
        for k in sorted(rows): w.writerow(rows[k])

if __name__ == '__main__':
    main()
