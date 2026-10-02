#!/usr/bin/env python3
"""test_authenticate.py - v43, v44: checks authenticate.py against three sayings whose standing is well known.
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
    ("China saying is not in the hadith layer", not china["hadith"]),
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
    ("collections outside the layer are listed apart from the critics", all(e["function"] == "collection" for e in china["collection"])
        and not any(e["function"] == "collection" for e in china["critics"])),
]
bad = [name for name, ok in checks if not ok]
for name, ok in checks: print("ok  " if ok else "FAIL", name)
sys.exit(1 if bad else 0)
