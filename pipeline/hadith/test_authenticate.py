#!/usr/bin/env python3
"""test_authenticate.py - v43 to v47: checks authenticate.py against three sayings whose standing is well known.
Run from the repo root: python3 pipeline/hadith/test_authenticate.py   (about 30 s; exits non-zero on failure)"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAYINGS = ["إنما الأعمال بالنيات وإنما لكل امرئ ما نوى",          # agreed upon
           "اطلبوا العلم ولو بالصين",                              # in the fabrication collections, not the layer
           "كنت كنزا مخفيا فأحببت أن أعرف فخلقت الخلق"]            # the critics quote it in another wording
out = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), *SAYINGS, "--json", "--repo", "."],
                     capture_output=True, text=True, check=True).stdout
niyya, china, kanz = json.loads(out)
ids = lambda L: {e["id"] for e in L}
checks = [
    ("niyya is found in al-Bukhari no. 1", "urn:hadith:0256Bukhari.Sahih:1" in ids(niyya["hadith"])),
    ("niyya carries al-Bukhari's grade", any(g["by"] == "al-Bukhari" for e in niyya["hadith"] for g in e["grades_classical"])),
    ("niyya has parallels in other collections", any(len(e.get("parallel_collections", [])) > 3 for e in niyya["hadith"])),
    ("China saying is not in the Six Books", not any(e["collection"].split(",")[0] in
        ("al-Bukhari", "Muslim", "Abu Dawud", "al-Tirmidhi", "al-Nasaʾi", "Ibn Maja") for e in china["hadith"])),
    ("China saying is in Ibn al-Jawzi's Mawduʿat", any(e["author"] == "Ibn al-Jawzi" for e in china["critics"])),
    ("critics come oldest first", [int(e["death_ah"]) for e in china["critics"]] == sorted(int(e["death_ah"]) for e in china["critics"])),
    ("modern grades are kept apart", china["modern"] and all(e["author"] == "al-Albani" for e in china["modern"])
        and not any(e["author"] == "al-Albani" for e in china["critics"])),
    ("al-Maqasid is searched once, not twice", len({e["id"] for e in china["critics"] if e["author"] == "al-Sakhawi"})
        == len([e for e in china["critics"] if e["author"] == "al-Sakhawi"])),
    ("hidden treasure: loose wording finds al-Sakhawi", "urn:openiti:0902Sakhawi.MaqasidHasana.JK001160-ara1:p03238" in ids(kanz["critics"])),
    ("hidden treasure: the verdict paragraph is attached", any("ابن تيمية" in e.get("then", "") for e in kanz["critics"])),
    ("hidden treasure is not in the hadith layer", not kanz["hadith"]),
]
# v44: the critics' verdicts as data
out2 = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), "طلب العلم فريضة على كل مسلم",
                       "أن رسول الله صلى الله عليه وسلم توضأ مرة مرة", "--json", "--repo", ".", "--limit", "50"],
                      capture_output=True, text=True, check=True).stdout
talab, wudu = json.loads(out2)
H = {e["id"]: e for e in talab["hadith"]}
im = H.get("urn:hadith:0273IbnMaja.Sunan:224", {}); tb = H.get("urn:hadith:0360Tabarani.MucjamKabir:10439", {})
checks += [
    ("Ibn Maja 224 carries al-Busiri's verdict on the chain", any("Busiri" in g["by"] and g.get("scope") == "chain" and "حفص" in g["grade"] for g in im.get("grades_classical", []))),
    ("al-Tabarani 10439 carries al-Haythami's verdict", any("Haythami" in g["by"] for g in tb.get("grades_classical", []))),
    ("every joined verdict names a record to cite", all(g.get("record") for e in talab["hadith"] for g in e["grades_classical"] if "scope" in g)),
    ("al-Albani on al-Tirmidhi is in the modern column only", any(e["grades_modern"] for e in wudu["hadith"])
        and not any("Albani" in g["by"] for e in wudu["hadith"] for g in e["grades_classical"])),
    ("hidden treasure: the critics' numbered entries are listed", {e["critic"] for e in kanz["entries"]} >= {"al-Sakhawi", "Mulla ʿAli al-Qari"}),
]
# v45: the authentication canon
checks += [
    ("China saying: at least 12 classical works now quote it", len({(e["author"], e["work"]) for e in china["critics"]}) >= 12),
    ("China saying: al-ʿAjluni's entry is in the sayings table", any(e["critic"] == "al-ʿAjluni" for e in china["entries"])),
    ("China saying: al-Albani's Jamiʿ verdict is in the modern entries only", bool(china["entries_modern"])
        and not any("Albani" in e["critic"] for e in china["entries"])),
]
# v46: the eight new collections in the hadith layer
out3 = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), "من قاد أعمى أربعين خطوة وجبت له الجنة",
                       "--json", "--repo", ".", "--no-modern"], capture_output=True, text=True, check=True).stdout
blind = json.loads(out3)[0]
ay = [e for e in blind["hadith"] if e["collection"].startswith("Abu Yaʿla")]
checks += [
    ("the hadith layer now has 21 collections", niyya["collections_searched"] == 21),
    ("niyya is found in Ibn Hibban's Sahih with his own claim of soundness", any(e["collection"].startswith("Ibn Hibban")
        and any(g["by"] == "Ibn Hibban" for g in e["grades_classical"]) for e in niyya["hadith"])),
    ("Abu Yaʿla's hadith of leading the blind carries al-Haythami's verdict", any("Haythami" in g["by"] and "كذاب" in g["grade"]
        for e in ay for g in e["grades_classical"])),
    ("no collection is left outside the layer", not china["collection"]),
]
# v47: more critics, the compilers' remarks, the modern column
out4 = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), "استغفروا لأخيكم وسلوا له التثبيت فإنه الآن يسأل",
                       "من لم يأخذ شاربه فليس منا", "--json", "--repo", ".", "--limit", "60"], capture_output=True, text=True, check=True).stdout
tathbit, sharib = json.loads(out4)
ad = next((e for e in tathbit["hadith"] if e["id"] == "urn:hadith:0275AbuDawudSijistani.Sunan:3221"), {})
aw = next((e for e in sharib["hadith"] if e["id"] == "urn:hadith:0360Tabarani.MucjamAwsat:522"), {})
checks += [
    ("Abu Dawud 3221 carries al-Nawawi's verdict on the chain", any("Nawawi" in g["by"] and "حسن" in g["grade"] for g in ad.get("grades_classical", []))),
    ("Abu Dawud 3221: al-Albani is in the modern column only", any("Albani" in g["by"] for g in ad.get("grades_modern", []))
        and not any("Albani" in g["by"] for g in ad.get("grades_classical", []))),
    ("Ahmad's hadith carry al-Arnaʾut in the modern column only", any("Arna" in g["by"] for e in tathbit["hadith"] + sharib["hadith"] for g in e["grades_modern"])
        and not any("Arna" in g["by"] or "Asad" in g["by"] for e in tathbit["hadith"] + sharib["hadith"] for g in e["grades_classical"])),
    ("al-Tabarani's own remark on Awsat 522 is a remark, not a grade", any("his own remark" in g["by"] and g["class"] == "uniqueness" for g in aw.get("grades_classical", []))),
]
# v48: the weak-narrator list has its record column; a reservation after a verdict is not filed as sound
import csv, gzip
with gzip.open("apparatus/hadith_links/weak_links.tsv.gz", "rt", encoding="utf-8") as fh: wl = list(csv.DictReader(fh, delimiter="\t"))
bl = list(csv.DictReader(open("apparatus/hadith_grades/ibnhajar_bulugh.tsv", encoding="utf-8"), delimiter="\t"))
checks += [
    ("every weak-narrator row names its Taqrib record", bool(wl) and all(r["taqrib_record"].startswith("urn:openiti:0852IbnHajar") for r in wl)),
    ("'وصححه الحاكم والراجح إرساله' is filed as disputed, not sound", all(r["class"] == "disputed" for r in bl if "الراجح إرساله" in r["verdict"]) and any("الراجح إرساله" in r["verdict"] for r in bl)),
]
# v49: the faster normalisation gives exactly the old result; a parallel and a one-processor run agree
sys.path.insert(0, os.path.join(HERE, "..", "search"))
import textnorm
sample = []
for p in ("apparatus/hadith/0279Tirmidhi.Sunan.jsonl.gz", "corpus/grading/0902Sakhawi.MaqasidHasana.jsonl.gz"):
    with gzip.open(p, "rt", encoding="utf-8") as fh: sample += [l for _, l in zip(range(3000), fh)]
one = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), SAYINGS[1], "--json", "--repo", "."],
                     capture_output=True, text=True, check=True, env={**os.environ, "AUTHENTICATE_JOBS": "1"}).stdout
many = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), SAYINGS[1], "--json", "--repo", "."],
                      capture_output=True, text=True, check=True).stdout
checks += [
    ("fast normalisation equals the reference formula on 6,000 lines",
     all(textnorm.norm(l) == textnorm.DIAC.sub("", l).translate(textnorm.MAP).lower() for l in sample)),
    ("a parallel run and a one-processor run give the same output", one == many and len(one) > 1000),
]
# v53: brief mode; al-Tirmidhi's missed hadith; ibn/bn matched as one word; the sijill is consulted first
V53 = ["إن العبد إذا أخطأ خطيئة نكتت في قلبه نكتة سوداء", "يا ابن آدم إنك ما دعوتني ورجوتني غفرت لك على ما كان منك ولا أبالي"]
full = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), *V53, "--json", "--repo", "."], capture_output=True, text=True, check=True).stdout
brief = subprocess.run([sys.executable, os.path.join(HERE, "authenticate.py"), *V53, "--brief", "--repo", "."], capture_output=True, text=True, check=True).stdout
j53 = json.loads(full)
checks += [
    ("the black spot hadith is in al-Tirmidhi's layer with his grade (v53)",
     any(e["id"].startswith("urn:hadith:0279Tirmidhi.Sunan:") and any("حسن صحيح" in (g.get("grade") or "") for g in e["grades_classical"]) for e in j53[0]["hadith"])),
    ("'يا ابن آدم' finds al-Tirmidhi's 'يا بن آدم' (v53)", any(e["id"].startswith("urn:hadith:0279Tirmidhi.Sunan:") for e in j53[1]["hadith"])),
    ("a saying already in the sijill is reported with its recorded standing (v53)",
     any(x["saying"] == "saying:black-spot" and x["standing"] for x in j53[0].get("sijill", []))),
    ("brief mode is short: under 5,000 characters for two sayings, a fifth of the full output or less, and names the sijill entry (v53)",
     0 < len(brief) < 5000 and "saying:black-spot" in brief and len(brief) * 5 < len(full)),
]
bad = [name for name, ok in checks if not ok]
for name, ok in checks: print("ok  " if ok else "FAIL", name)
sys.exit(1 if bad else 0)
