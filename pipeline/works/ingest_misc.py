#!/usr/bin/env python3
"""v10: import typed .txt/.docx uploads and archive.org OCR of two critical editions. Never retyped.
Each source file is checked against archive.org's md5 and copied byte-exact (src/).
  txt  -> one JSONL row per non-empty line (text_raw = the line exactly, BOM removed from the first).
  docx -> one row per Word paragraph (w:p), text joined from its w:t runs.
  ocr  -> one row per scanned leaf, from archive.org's hocr_searchtext + pageindex, with the printed
          page number archive.org detected (page_numbers.json). source_type = ocr_uncorrected.
Usage: python3 ingest_misc.py --manifest manifest_misc.json --outdir out
"""
import argparse,gzip,hashlib,json,re,shutil,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
def docx_paras(p):
    root=ET.fromstring(zipfile.ZipFile(p).read("word/document.xml"))
    for para in root.iter(W+"p"):
        yield "".join(t.text or "" for t in para.iter(W+"t"))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest"); ap.add_argument("--outdir"); a=ap.parse_args()
    man=json.load(open(a.manifest,encoding="utf-8")); out=Path(a.outdir); (out/"src").mkdir(parents=True,exist_ok=True); (out/"jsonl").mkdir(exist_ok=True)
    cat={"works":{}}
    for w in man:
        srcs=[]
        for s in w["files"]:
            p=Path(s["local"]); raw=p.read_bytes()
            if s.get("md5"): assert hashlib.md5(raw).hexdigest()==s["md5"],(w["key"],p)
            shutil.copyfile(p,out/"src"/f"{w['key']}__{p.name.split('__',1)[-1]}")
            srcs.append({"file":s["name"],"item":s["item"],"md5":hashlib.md5(raw).hexdigest(),"sha256":hashlib.sha256(raw).hexdigest()})
        rows=[]
        for s in w["files"]:
            if s.get("role")!="text": continue
            p=Path(s["local"]); vol=s.get("vol")
            if w["kind"]=="txt":
                lines=p.read_bytes().decode("utf-8-sig").splitlines()
                for i,l in enumerate(lines,1):
                    if l.strip(): rows.append({"vol":vol,"line":i,"text_raw":l,"text":re.sub(r"\s+"," ",l).strip()})
            elif w["kind"]=="docx":
                for i,t in enumerate(docx_paras(p),1):
                    if t.strip(): rows.append({"vol":vol,"para":i,"text_raw":t,"text":re.sub(r"\s+"," ",t).strip()})
        if w["kind"]=="ocr":
            base=w["ocr_base"]; t=gzip.open(base+"_hocr_searchtext.txt.gz","rt",encoding="utf-8").read()
            pi=json.loads(gzip.open(base+"_hocr_pageindex.json.gz","rt").read())
            pn={p["leafNum"]:p.get("pageNumber") for p in json.load(open(base+"_page_numbers.json"))["pages"]}
            for leaf,(s0,e0,_,_) in enumerate(pi,1):
                rows.append({"leaf":leaf,"printed_page":pn.get(leaf) or None,"text_raw":t[s0:e0],"text":re.sub(r"\s+"," ",t[s0:e0]).strip()})
        with open(out/"jsonl"/f"{w['key']}.jsonl","w",encoding="utf-8") as fo:
            for n,r in enumerate(rows,1):
                r={"id":f"urn:lib:{w['key']}:{n:05d}","work":w["work"],**r,"provenance":{"source":"archive.org","items":sorted({s['item'] for s in w['files']}),"method":"imported","source_type":w["source_type"],"status":"unverified"}}
                fo.write(json.dumps(r,ensure_ascii=False)+"\n")
        cat["works"][w["key"]]={k:w[k] for k in ("work","author","attribution","category","source_type","note")}|{"rows":len(rows),"sources":srcs}
        print(w["key"],len(rows))
    (out/"misc_catalog.json").write_text(json.dumps(cat,ensure_ascii=False,indent=1),encoding="utf-8")
main()
