#!/usr/bin/env python3
"""Import Ganjoor works (other than the Mathnawi) by script, never retyped.
Walks each category tree in catalog order (_cat.json ChildCats / Poems), keeps only the text
(verse lines paired by Position, prose paragraphs, centered band lines), drops all machine
summaries (PoemSummary, CoupletSummary) and logs every dropped key. Records commit + sha256 per file.
Usage: python3 ingest_works.py --data ganjoor-data --outdir out
"""
import argparse,hashlib,json,subprocess,unicodedata
from pathlib import Path
WORKS=[ # (ganjoor folder, urn work, unit prefix per child cat or None, title)
 ("poets/moulavi/shams/ghazalsh","rumi.diwan","gh","Divan-i Shams: ghazals"),
 ("poets/moulavi/shams/robaeesh","rumi.diwan","rb","Divan-i Shams: quatrains"),
 ("poets/moulavi/shams/tarjeeat","rumi.diwan","tj","Divan-i Shams: tarji'at"),
 ("poets/moulavi/shams/mostadrakat","rumi.diwan","ms","Divan-i Shams: mustadrakat"),
 ("poets/moulavi/fhmfh","rumi.fihi","d","Fihi ma fihi"),
 ("poets/moulavi/7m","rumi.majalis","m","Majalis-i sab'a"),
 ("poets/baha/maaref","bahawalad.maarif","j","Baha' Walad, Ma'arif"),
 ("poets/valad/valadname","sultanwalad.waladnama","s","Sultan Walad, Waladnama"),
]
KEEP={"VOrder","Position","Text"}
def walk(repo,rel):
    cat=json.load(open(repo/rel/"_cat.json",encoding="utf-8"))
    for p in cat.get("Poems") or []:
        yield rel,cat["Title"],p
    for c in cat.get("ChildCats") or []:
        sub=rel+"/"+c["FullUrl"].rstrip("/").split("/")[-1]
        yield from walk(repo,sub)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--outdir",default="out"); a=ap.parse_args()
    repo=Path(a.data); out=Path(a.outdir); out.mkdir(exist_ok=True)
    sha=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    summary={"source":"ganjoor-data","commit":sha,"works":{}}
    for folder,work,pre,title in WORKS:
        fo=open(out/f"{work}.{pre}.jsonl","w",encoding="utf-8"); rep={"title":title,"folder":folder,"poems_in_catalog":0,"poems_found":0,"missing_files":[],
             "units":{},"dropped_keys":set(),"warnings":[],"files":{}}
        seq=0; pnum=0
        for rel,cattitle,p in walk(repo,folder):
            rep["poems_in_catalog"]+=1; slug=p["FullUrl"].rstrip("/").split("/")[-1]
            f=repo/rel/f"{slug}.json"
            if not f.exists(): rep["missing_files"].append(str(rel)+"/"+slug); continue
            raw=f.read_bytes(); d=json.loads(raw); rep["poems_found"]+=1; pnum+=1
            rep["dropped_keys"]|= {k for k in d if k not in ("Verses","Title","Metre","RhymeLetters")}
            rep["files"][str(f.relative_to(repo))]=hashlib.sha256(raw).hexdigest()
            sub=rel[len(folder):].strip("/")
            num=slug[2:] if slug.startswith("sh") else slug
            base=f"urn:sufi:{work}:{pre}{(sub+'.') if sub else ''}{num}"
            vs=sorted(d["Verses"],key=lambda v:v.get("VOrder",0)); k=0; i=0; pk=0
            for v in vs: rep["dropped_keys"]|={"verse:"+x for x in v if x not in KEEP}
            while i<len(vs):
                v=vs[i]; pos=v.get("Position"); t=v.get("Text","")
                if pos=="Comment": i+=1; continue
                if pos=="Right" and i+1<len(vs) and vs[i+1].get("Position")=="Left":
                    k+=1; unit={"unit_type":"bayt","hemistichs":[t,vs[i+1]["Text"]],"id":f"{base}.b{k:03d}"}; i+=2
                elif pos=="Paragraph":
                    pk+=1; unit={"unit_type":"para","text":t,"id":f"{base}.p{pk:03d}"}; i+=1
                elif pos in("CenteredVerse1",) and i+1<len(vs) and vs[i+1].get("Position")=="CenteredVerse2":
                    k+=1; unit={"unit_type":"band_bayt","hemistichs":[t,vs[i+1]["Text"]],"id":f"{base}.b{k:03d}"}; i+=2
                else:
                    k+=1; unit={"unit_type":"single_line","text":t,"position":pos,"id":f"{base}.b{k:03d}"}; i+=1
                    rep["warnings"].append(f"{rel}/{slug}: unpaired {pos} at VOrder {v.get('VOrder')}")
                for x in unit.get("hemistichs",[unit.get("text","")]):
                    if x!=unicodedata.normalize("NFC",x): rep["warnings"].append(f"{rel}/{slug}: not NFC (kept)"); break
                seq+=1; rep["units"][unit["unit_type"]]=rep["units"].get(unit["unit_type"],0)+1
                unit.update({"work":work,"part":pre,"subdivision":sub or None,"poem_number":num,"poem_title":d.get("Title"),"ganjoor_metre":d.get("Metre"),"ganjoor_rhyme":d.get("RhymeLetters"),"section_title":cattitle,"seq":seq,
                    "provenance":{"source":"ganjoor-data","commit":sha,"file":str(f.relative_to(repo)),"method":"imported","status":"unverified"}})
                fo.write(json.dumps(unit,ensure_ascii=False)+"\n")
        fo.close(); rep["dropped_keys"]=sorted(rep["dropped_keys"])
        (out/f"{work}.{pre}_report.json").write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding="utf-8")
        summary["works"][f"{work}.{pre}"]={"title":title,"poems":rep["poems_found"],"catalog":rep["poems_in_catalog"],"missing":len(rep["missing_files"]),"units":rep["units"],"warnings":len(rep["warnings"])}
        print(title,summary["works"][f"{work}.{pre}"])
    (out/"works_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=1),encoding="utf-8")
main()
