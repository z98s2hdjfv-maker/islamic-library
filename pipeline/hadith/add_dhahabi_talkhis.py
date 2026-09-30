#!/usr/bin/env python3
"""
add_dhahabi_talkhis.py - v35: al-Dhahabi's verdicts on al-Hakim's Mustadrak (his Talkhis), as classical grades.

Source: corpus/grading/0405HakimNaysaburi.Mustadrak.jsonl.gz, the Shamela edition that prints al-Dhahabi's Talkhis
after each hadith under the heading "[التعليق - من تلخيص الذهبي]", followed by "N - <verdict>".
Join: each verdict is attached to the hadith printed just before it, found in the hadith layer
(apparatus/hadith/0405HakimNaysaburi.Mustadrak.jsonl.gz) by shared 5-word sequences; accepted when at least half of
the printed hadith's sequences match (match column). Numbers are not used to join: the two editions number a few
hadith differently. Tested 2026-09-30: 5,618 of 5,711 verdicts joined; 5,538 of them also agree on the number.
Output: apparatus/hadith_grades/dhahabi_talkhis_mustadrak.tsv
  hadith_id (empty if not joined), layer_number, dhahabi_no, verdict (his words), match, talkhis_record, hadith_record
build_index.py adds joined verdicts to the hadith's grades as "al-Dhahabi (Talkhis): <verdict>" (classical layer).
Usage: python3 pipeline/hadith/add_dhahabi_talkhis.py --repo .
"""
import argparse, collections, csv, gzip, json, os, re, sys

def main(repo):
    os.chdir(repo)
    sys.path.insert(0, "pipeline/search"); from textnorm import norm
    W = re.compile(r"[ء-ي]{2,}")
    recs = [json.loads(l) for l in gzip.open("corpus/grading/0405HakimNaysaburi.Mustadrak.jsonl.gz", "rt", encoding="utf-8")]
    units = {}
    for l in gzip.open("corpus/hadith/0405HakimNaysaburi.Mustadrak.jsonl.gz", "rt", encoding="utf-8"):
        r = json.loads(l); units[r["id"]] = r.get("text", "")
    lay = []; idx = collections.defaultdict(list)
    for l in gzip.open("apparatus/hadith/0405HakimNaysaburi.Mustadrak.jsonl.gz", "rt", encoding="utf-8"):
        h = json.loads(l); ws = W.findall(norm(" ".join(units.get(u, "") for u in h["source_ids"])))
        k = len(lay); lay.append((h["id"], str(h["number"]), ws))
        for i in range(len(ws) - 4): idx[" ".join(ws[i:i + 5])].append(k)
    out = []; ok = 0
    for i,r in enumerate(recs):
        if not (r['kind']=='heading' and 'تلخيص الذهبي' in r['text_raw']): continue
        nxt=next((x for x in recs[i+1:i+3] if x['kind']=='para'),None)
        prv=next((x for x in reversed(recs[max(0,i-4):i]) if x['kind']=='para'),None)
        if not nxt or not prv: continue
        m=re.match(r'\s*(\d+)\s*-\s*(.*)',nxt['text'])
        if not m: continue
        ws=W.findall(norm(prv['text']))
        v=collections.Counter()
        for j in range(len(ws)-4):
            for k in set(idx.get(' '.join(ws[j:j+5]),())): v[k]+=1
        best,sc=(v.most_common(1)[0] if v else (None,0))
        share=sc/max(1,len(ws)-4)
        hid=lay[best][0] if best is not None and share>=.5 else ''
        ok+=bool(hid)
        out.append(dict(dhahabi_no=int(m.group(1)),verdict=m.group(2).strip(),talkhis_record=nxt['id'],hadith_record=prv['id'],
                        hadith_id=hid,layer_number=lay[best][1] if hid else '',match=round(share,2)))

    os.makedirs("apparatus/hadith_grades", exist_ok=True)
    cols = ["hadith_id", "layer_number", "dhahabi_no", "verdict", "match", "talkhis_record", "hadith_record"]
    with open("apparatus/hadith_grades/dhahabi_talkhis_mustadrak.tsv", "w", encoding="utf-8") as f:
        c = csv.writer(f, delimiter="\t", lineterminator="\n"); c.writerow(cols)
        for o in out: c.writerow([o[k] for k in cols])
    print(len(out), "verdicts;", ok, "joined to the hadith layer")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); main(os.path.abspath(ap.parse_args().repo))
