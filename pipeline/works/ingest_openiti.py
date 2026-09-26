#!/usr/bin/env python3
"""v8: import Arabic works of al-Ghazali, al-Jilani and Ibn 'Arabi from OpenITI (GitHub, pinned commits).
Never retyped. For every text version:
  * the OpenITI file is copied byte-exact (raw/), with sha256;
  * a paragraph JSONL is derived: '# ' starts a paragraph, '~~' continues it, '### |..' are headings,
    PageVxxPyyy markers give volume/page. 'text_raw' keeps the line content exactly (joined by \n);
    'text' removes page/milestone markers and joins lines with spaces (derived, for search only).
Each work gets: attribution flag, source_type (typed | ocr_uncorrected | scraped_incomplete), and one
'primary' version (typed over OCR; OpenITI '.completed'/'.mARkdown' first; then longest).
Usage: python3 ingest_openiti.py --oiti DIR --outdir out
"""
import argparse,hashlib,json,re,subprocess,shutil
from pathlib import Path
REPOS={"0525AH":"data/0505Ghazali","0575AH":"data/0561CabdQadirJilani","0650AH":"data/0638IbnCarabi"}
S,D,X="secure","doubtful","spurious_attested"
ATTR={ # work uri -> (attribution, note)
 "0505Ghazali.SirrCalamin":(X,"Sirr al-'alamin: generally rejected as al-Ghazali's"),
 "0505Ghazali.MinhajCabidin":(D,"Minhaj al-'abidin: attribution disputed"),
 "0505Ghazali.RaddJamil":(D,"al-Radd al-jamil: attribution disputed"),
 "0505Ghazali.MacarijQuds":(D,"Ma'arij al-quds: attribution disputed"),
 "0505Ghazali.KimiyaSacada":(D,"Arabic Kimiya: relation to the Persian original to be checked"),
 "0561CabdQadirJilani.Diwan":(D,"Arabic diwan attributed to al-Jilani"),
 "0561CabdQadirJilani.SirrAsrar":(D,"Sirr al-asrar: attribution debated"),
 "0561CabdQadirJilani.Tafsir":(D,"Tafsir al-Jilani (publ. 2009): attribution doubtful"),
 "0638IbnCarabi.Tafsir":(X,"Ta'wilat usually assigned to 'Abd al-Razzaq al-Qashani"),
}
ALIAS={"0561CabdQadirJilani.AdabSuluk":"= Futuh al-ghayb (Adab al-suluk wa-l-tawassul ila manazil al-muluk)"}
def stype(name):
    if re.search(r"\.(Kraken|EScr|AOCP)",name): return "ocr_uncorrected"
    if ".Tafsir0" in name: return "scraped_incomplete"
    return "typed"
PAGE=re.compile(r"PageV(\d+)P(\d+)"); MS=re.compile(r"\bms\d+\b")
def parse(txt):
    body=txt.split("#META#Header#End#",1)[-1].splitlines()
    meta={}
    for l in txt.split("#META#Header#End#",1)[0].splitlines():
        m=re.match(r"#META#\s*(.+?)\s*(?:::|:)\s*(.*)$",l)
        if m: meta[m.group(1).strip()]=m.group(2).strip()
    paras=[]; cur=None; vol,page=None,None; heads=[]
    def flush():
        nonlocal cur
        if cur: paras.append(cur); cur=None
    for l in body:
        if l.startswith("### |"):
            flush(); lvl=len(re.match(r"### (\|+)",l).group(1)); t=l[4+lvl:].strip()
            heads=heads[:lvl-1]+[t]; paras.append({"kind":"heading","level":lvl,"text_raw":l,"vol":vol,"page":page}); continue
        if l.startswith("# "): flush(); cur={"kind":"para","lines":[l[2:]],"vol":vol,"page":page,"heads":list(heads)}
        elif l.startswith("~~") and cur: cur["lines"].append(l[2:])
        elif l.strip():
            flush(); cur={"kind":"para","lines":[l],"vol":vol,"page":page,"heads":list(heads)}
        for m in PAGE.finditer(l):
            vol,page=int(m.group(1)),int(m.group(2))
    flush(); return meta,paras
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--oiti",required=True); ap.add_argument("--outdir",default="out"); a=ap.parse_args()
    root=Path(a.oiti); out=Path(a.outdir); (out/"raw").mkdir(parents=True,exist_ok=True); (out/"jsonl").mkdir(exist_ok=True)
    catalog={"source":"OpenITI (github.com/OpenITI)","license":"CC BY-NC-SA 4.0","repos":{},"works":{}}
    for repo,folder in REPOS.items():
        sha=subprocess.check_output(["git","-C",str(root/repo),"rev-parse","HEAD"],text=True).strip(); catalog["repos"][repo]=sha
        for wd in sorted((root/repo/folder).iterdir()):
            if not wd.is_dir(): continue
            work=wd.name; vers=[]
            for f in sorted(wd.iterdir()):
                if f.suffix in (".yml",".md") or not re.search(r"-(ara|per)\d",f.name): continue
                raw=f.read_bytes(); txt=raw.decode("utf-8")
                meta,paras=parse(txt)
                shutil.copyfile(f,out/"raw"/f.name)
                pages=sorted({(p["vol"],p["page"]) for p in paras if p["page"]})
                n=0
                with open(out/"jsonl"/f"{f.name}.jsonl","w",encoding="utf-8") as fo:
                    for i,p in enumerate(paras,1):
                        rec={"id":f"urn:openiti:{f.name}:p{i:05d}","work":work,"version":f.name,"kind":p["kind"],"vol":p["vol"],"page_before":p["page"]}
                        if p["kind"]=="heading": rec.update(level=p["level"],text_raw=p["text_raw"])
                        else:
                            rec["text_raw"]="\n".join(p["lines"]); rec["headings"]=p["heads"]
                            rec["text"]=re.sub(r"\s+"," ",MS.sub("",PAGE.sub("",rec["text_raw"]))).strip()
                        rec["provenance"]={"source":"OpenITI","repo":repo,"commit":sha,"file":str(f.relative_to(root/repo)),"method":"imported","status":"unverified"}
                        fo.write(json.dumps(rec,ensure_ascii=False)+"\n"); n+=1
                ed={k:v for k,v in meta.items() if re.search(r"EdEDITOR|EdPUBLISHER|EdPLACE|EdYEAR|المحقق|الناشر|الطبعة|عدد الأجزاء|Origin",k)}
                vers.append({"file":f.name,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"source_type":stype(f.name),
                    "completed":f.name.endswith((".completed",".mARkdown")),"units":n,"pages":len(pages),"edition_meta":ed})
            if not vers: continue
            rank=lambda v:(v["source_type"]=="typed",v["completed"],v["bytes"])
            prim=max(vers,key=rank)["file"]
            at=ATTR.get(work,(S,""))
            catalog["works"][work]={"attribution":at[0],"attribution_note":at[1],"alias":ALIAS.get(work),"primary":prim,"versions":vers}
            print(work,at[0],len(vers),"versions; primary",prim)
    (out/"openiti_catalog.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=1),encoding="utf-8")
main()
