#!/usr/bin/env python3
"""v7: import further Ganjoor works by script, never retyped. Same unit logic as ingest_works.py (v6):
verse lines paired by Position, prose paragraphs, centered band lines; machine summaries dropped and
logged; commit + sha256 per file. Adds: 'attribution' (secure | doubtful | spurious_attested) per work,
and root-level single poems (e.g. Attar's Futuwwat-nama) as their own work.
Usage: python3 ingest_works2.py --data ganjoor-data --outdir out
"""
import argparse,hashlib,json,subprocess,unicodedata
from pathlib import Path
S,D,X="secure","doubtful","spurious_attested"
# (ganjoor folder or single poem file stem, urn work, unit prefix, title, attribution, note)
WORKS=[
 ("poets/ghazzali/kimia","ghazali.kimiya","k","al-Ghazali, Kimiya-yi sa'adat",S,""),
 ("poets/gilani/ghazalgi","jilani.diwan","gh","Divan attributed to 'Abd al-Qadir al-Jilani: ghazals",D,"Persian divan; attribution to al-Jilani widely doubted"),
 ("poets/meybodi/kashfol-asrar","maybudi.kashf","t","Maybudi, Kashf al-asrar wa 'uddat al-abrar",S,"Qur'an commentary (tafsir), sura order"),
 ("poets/eraghi/lamaat","iraqi.lamaat","l","'Iraqi, Lama'at",S,""),
 ("poets/eraghi/divane","iraqi.diwan","d","'Iraqi, Divan",S,""),
 ("poets/eraghi/oshaghname","iraqi.ushshaqnama","u","'Iraqi, 'Ushshaq-nama",D,"attribution to 'Iraqi questioned by some scholars"),
 ("poets/eraghi/estelahat","iraqi.istilahat","i","'Iraqi, Risala-yi istilahat",D,"attribution questioned"),
 ("poets/ouhad/robaee","awhad.rubaiyat","rb","Awhad al-Din Kirmani, ruba'is",S,""),
 ("poets/shabestari/golshaneraz","shabistari.gulshan","g","Shabistari, Gulshan-i raz",S,""),
 ("poets/shabestari/hagholyaghin","shabistari.haqqalyaqin","h","Shabistari, Haqq al-yaqin",S,""),
 ("poets/shabestari/merat","shabistari.mirat","m","Shabistari, Mir'at al-muhaqqiqin",D,"attribution debated"),
 ("poets/shabestari/saadatname","shabistari.saadatnama","s","Shabistari, Sa'adat-nama",S,""),
 ("poets/shabestari/kanzolhaghayegh","shabistari.kanz","k","Kanz al-haqa'iq (attributed to Shabistari)",D,"attribution debated"),
 ("poets/shabestari/marateb","shabistari.maratib","r","Maratib al-'arifin (attributed to Shabistari)",D,"root-level single text"),
 ("poets/jami/divanj","jami.diwan","d","Jami, Divan",S,""),
 ("poets/jami/7ourang","jami.haftawrang","h","Jami, Haft awrang",S,""),
 ("poets/jami/baharestan","jami.baharistan","b","Jami, Baharistan",S,""),
 ("poets/jami/arbaeen","jami.arbain","a","Jami, Risala-yi arba'in",S,"forty hadith"),
 ("poets/sanaee/hadighe","sanai.hadiqa","h","Sana'i, Hadiqat al-haqiqa",S,""),
 ("poets/sanaee/divans","sanai.diwan","d","Sana'i, Divan",S,""),
 ("poets/sanaee/tariq","sanai.tariq","t","Tariq al-tahqiq (attributed to Sana'i)",X,"now usually assigned to Ahmad b. al-Hasan Nakhjawani"),
 ("poets/attar/manteghotteyr","attar.mantiq","m","'Attar, Mantiq al-tayr",S,""),
 ("poets/attar/elahiname","attar.ilahinama","i","'Attar, Ilahi-nama",S,""),
 ("poets/attar/mosibatname","attar.musibatnama","u","'Attar, Musibat-nama",S,""),
 ("poets/attar/asrarname","attar.asrarnama","a","'Attar, Asrar-nama",S,""),
 ("poets/attar/tazkerat-ol-ouliya","attar.tadhkira","t","'Attar, Tadhkirat al-awliya",S,""),
 ("poets/attar/divana","attar.diwan","d","'Attar, Divan",S,""),
 ("poets/attar/mokhtarname","attar.mukhtarnama","k","'Attar, Mukhtar-nama",S,""),
 ("poets/attar/khosroname","attar.khusrawnama","x","'Attar, Khusraw-nama",D,"attribution debated"),
 ("poets/attar/pandname","attar.pandnama","p","Pand-nama (attributed to 'Attar)",X,"pseudo-'Attar"),
 ("poets/attar/fn","attar.futuwwatnama","f","Futuwwat-nama (attributed to 'Attar)",X,"pseudo-'Attar; root-level single text"),
]+[(f"poets/attar/{f}",f"attar.{w}",p,f"{t} (attributed to 'Attar)",X,"pseudo-'Attar (later 'Attar of Tun and others)") for f,w,p,t in [
 ("bolbolname","bulbulnama","bb","Bulbul-nama"),("30fasl","siyfasl","sf","Si fasl"),("bayanolershad","bayanalirshad","bi","Bayan al-irshad"),
 ("bisarname","bisarnama","bs","Bi-sar-nama"),("hylajname","hilajnama","hj","Hilaj-nama"),("mazhar","mazhar","mz","Mazhar"),
 ("jz","jawharaldhat","jz","Jawhar al-dhat"),("ma","mazharalajaib","ma","Mazhar al-'aja'ib"),("vaslatname","wuslatnama","ws","Wuslat-nama"),
 ("na","nuzhatalahbab","na","Nuzhat al-ahbab"),("oshtorname","ushturnama","us","Ushtur-nama")]]
KEEP={"VOrder","Position","Text"}
def walk(repo,rel):
    cat=json.load(open(repo/rel/"_cat.json",encoding="utf-8"))
    for p in cat.get("Poems") or []:
        yield rel,cat["Title"],p
    for c in cat.get("ChildCats") or []:
        sub=rel+"/"+c["FullUrl"].rstrip("/").split("/")[-1]
        yield from walk(repo,sub)
def items(repo,folder):
    if (repo/folder).is_dir(): yield from walk(repo,folder); return
    parent=folder.rsplit("/",1)[0]; cat=json.load(open(repo/parent/"_cat.json",encoding="utf-8"))
    for p in cat.get("Poems") or []:
        if p["FullUrl"].rstrip("/").split("/")[-1]==folder.rsplit("/",1)[1]: yield parent,cat["Title"],p
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--outdir",default="out"); a=ap.parse_args()
    repo=Path(a.data); out=Path(a.outdir); out.mkdir(exist_ok=True)
    sha=subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    summary={"source":"ganjoor-data","commit":sha,"works":{}}
    for folder,work,pre,title,attr,note in WORKS:
        single=not (repo/folder).is_dir()
        fo=open(out/f"{work}.{pre}.jsonl","w",encoding="utf-8"); rep={"title":title,"folder":folder,"attribution":attr,"attribution_note":note,"poems_in_catalog":0,"poems_found":0,"missing_files":[],
             "units":{},"dropped_keys":set(),"warnings":[],"files":{}}
        seq=0
        for rel,cattitle,p in items(repo,folder):
            rep["poems_in_catalog"]+=1; slug=p["FullUrl"].rstrip("/").split("/")[-1]
            f=repo/rel/f"{slug}.json"
            if not f.exists(): rep["missing_files"].append(str(rel)+"/"+slug); continue
            raw=f.read_bytes(); d=json.loads(raw); rep["poems_found"]+=1
            rep["dropped_keys"]|= {k for k in d if k not in ("Verses","Title","Metre","RhymeLetters")}
            rep["files"][str(f.relative_to(repo))]=hashlib.sha256(raw).hexdigest()
            sub="" if single else rel[len(folder):].strip("/")
            num="1" if single else (slug[2:] if slug.startswith("sh") else slug)
            base=f"urn:sufi:{work}:{pre}{(sub.replace('/','.')+'.') if sub else ''}{num}"
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
                    "attribution":attr,
                    "provenance":{"source":"ganjoor-data","commit":sha,"file":str(f.relative_to(repo)),"method":"imported","status":"unverified"}})
                fo.write(json.dumps(unit,ensure_ascii=False)+"\n")
        fo.close(); rep["dropped_keys"]=sorted(rep["dropped_keys"])
        (out/f"{work}.{pre}_report.json").write_text(json.dumps(rep,ensure_ascii=False,indent=1),encoding="utf-8")
        summary["works"][f"{work}.{pre}"]={"title":title,"attribution":attr,"poems":rep["poems_found"],"catalog":rep["poems_in_catalog"],"missing":len(rep["missing_files"]),"units":rep["units"],"warnings":len(rep["warnings"])}
        print(title,summary["works"][f"{work}.{pre}"],flush=True)
    (out/"works_summary_v7.json").write_text(json.dumps(summary,ensure_ascii=False,indent=1),encoding="utf-8")
main()
