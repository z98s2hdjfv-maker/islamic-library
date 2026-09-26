#!/usr/bin/env python3
"""Rebuild step (2026-09-25): put the Nicholson IDs into the JSONL made by ingest_full.py.
The numbering comes from mathnawi_book<N>.tsv (aligned with masnavi.net on 2026-09-25).
Rows are joined on ganjoor_seq; hemistichs must match the TSV exactly or the script stops.
Usage: python3 apply_nicholson.py --jsonl-dir build --tsv-dir . --outdir out
"""
import argparse,csv,json,re
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("--jsonl-dir",required=True); ap.add_argument("--tsv-dir",default="."); ap.add_argument("--outdir",required=True); a=ap.parse_args()
out=Path(a.outdir); out.mkdir(exist_ok=True)
for b in range(1,7):
    rows=list(csv.reader(open(Path(a.tsv_dir)/f"mathnawi_book{b}.tsv",encoding="utf-8"),delimiter="\t",quoting=csv.QUOTE_NONE))
    hdr=rows[0]; T={int(r[1]):dict(zip(hdr,r)) for r in rows[1:]}
    ncol=[h for h in hdr if h.startswith("nicholson")][0]
    n=0; fo=open(out/f"mathnawi_book{b}.jsonl","w",encoding="utf-8")
    for line in open(Path(a.jsonl_dir)/f"mathnawi_book{b}.jsonl",encoding="utf-8"):
        r=json.loads(line); t=T[r["ganjoor_seq"]]
        h=r["text"]["source"]["hemistichs"]
        assert int(t["section"])==r["concordance"][0]["section"] and int(t["line"])==r["concordance"][0]["line"], (b,r["ganjoor_seq"])
        assert h[0]==t["hemistich_1"] and (h[1] if len(h)>1 else "")==t["hemistich_2"], (b,r["ganjoor_seq"])
        num=t[ncol]; suffix=re.sub(r"^\d+","",t["id"].rsplit(".b",1)[1])
        r["id"]=t["id"]
        r["concordance"][1]={"edition":"nicholson_gibb","number":int(num) if num.isdigit() else None,
            "present":"interpolation_candidate" if suffix else "aligned_unverified","via":"masnavi.net (Nicholson numbering)"}
        if suffix: r["provenance"]["status"]="interpolation_candidate"
        fo.write(json.dumps(r,ensure_ascii=False)+"\n"); n+=1
    fo.close(); assert n==len(T); print(b,n,"rows ok")
