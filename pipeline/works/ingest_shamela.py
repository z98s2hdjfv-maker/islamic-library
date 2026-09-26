#!/usr/bin/env python3
"""v9: import Shamela book files (.bok, MS Access) found on archive.org. Never retyped.
Each archive.org file is checked against archive.org's md5, unpacked, and the .bok is copied byte-exact.
From the .bok: Main (card: title, author, editor, publisher, edition) and the text table b<N>
(id, nass, part, page[, hno]) -> one JSONL row per Shamela page-record. 'text_raw' is nass exactly as stored;
'text' and 'footnotes' are derived (split at Shamela's '______' footnote rule; CR -> LF).
Headings come from table t<N> (id = first b-row of the heading, lvl = depth).
Usage: python3 ingest_shamela.py --dl DL_DIR --x EXTRACT_DIR --manifest manifest.json --outdir out
"""
import argparse,csv,hashlib,io,json,re,shutil,subprocess
from pathlib import Path
csv.field_size_limit(10**9)
def num(x):
    if x in (None,""): return None
    return int(x) if str(x).isdigit() else x
def table(f,t): return list(csv.DictReader(io.StringIO(subprocess.check_output(["mdb-export",str(f),t],text=True))))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dl"); ap.add_argument("--x"); ap.add_argument("--manifest"); ap.add_argument("--outdir"); a=ap.parse_args()
    man=json.load(open(a.manifest,encoding="utf-8")); out=Path(a.outdir); (out/"bok").mkdir(parents=True,exist_ok=True); (out/"jsonl").mkdir(exist_ok=True)
    cat={"source":"archive.org uploads of al-Maktaba al-Shamila .bok files","works":{}}
    for w in man:
        rar=Path(a.dl)/w["archive_file"]; md5=hashlib.md5(rar.read_bytes()).hexdigest()
        assert md5==w["archive_md5"],(w["key"],md5)
        bok=next(p for p in (Path(a.x)/rar.stem).rglob("*.bok") if p.stat().st_size>0)
        raw=bok.read_bytes(); shutil.copyfile(bok,out/"bok"/f"{w['key']}.bok")
        tabs=subprocess.check_output(["mdb-tables","-1",str(bok)],text=True).split()
        bt=[t for t in tabs if re.fullmatch(r"b\d+",t)][0]; tt="t"+bt[1:]
        m=table(bok,"Main")[0]; rows=table(bok,bt); heads=table(bok,tt) if tt in tabs else []
        hmap={}
        for h in heads: hmap.setdefault(int(h["id"]),[]).append((int(h["lvl"] or 1),h["tit"]))
        path=[]; n=0
        with open(out/"jsonl"/f"{w['key']}.jsonl","w",encoding="utf-8") as fo:
            for r in sorted(rows,key=lambda r:int(r["id"])):
                i=int(r["id"])
                for lvl,t in hmap.get(i,[]): path=path[:lvl-1]+[t]
                nass=r["nass"]; txt=nass.replace("\r\n","\n").replace("\r","\n")
                body,_,fn=txt.partition("\n__________")
                rec={"id":f"urn:shamela:{w['key']}:r{i:05d}","work":w["work"],"shamela_row":i,"part":num(r.get("part") or 1),"page":num(r.get("page")),
                     "headings":list(path),"text_raw":nass,"text":body.strip(),"footnotes":fn.strip("_\n ") or None,
                     "provenance":{"source":"archive.org","item":w["item"],"file":w["archive_file_orig"],"md5":md5,"bok_sha256":hashlib.sha256(raw).hexdigest(),"method":"imported","status":"unverified"}}
                fo.write(json.dumps(rec,ensure_ascii=False)+"\n"); n+=1
        card={k:(m.get(k) or "").replace("\r","\n") for k in ("Bk","Betaka","Auth","Inf")}
        cat["works"][w["key"]]={**{k:w[k] for k in ("work","author","attribution","category","note","item")},"rows":n,"parts":len({r.get('part') or 1 for r in rows}),"headings":len(heads),"card":card,"bok_sha256":hashlib.sha256(raw).hexdigest(),"archive_md5":md5}
        print(w["key"],n,"rows",len(heads),"headings")
    (out/"shamela_catalog.json").write_text(json.dumps(cat,ensure_ascii=False,indent=1),encoding="utf-8")
main()
