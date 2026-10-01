#!/usr/bin/env python3
"""test_authenticate.py - v43: checks authenticate.py against three sayings whose standing is well known.
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
bad = [name for name, ok in checks if not ok]
for name, ok in checks: print("ok  " if ok else "FAIL", name)
sys.exit(1 if bad else 0)
