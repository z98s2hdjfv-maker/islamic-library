#!/usr/bin/env python3
"""
test_search.py - v32 smoke test for a search index (full or sample). Exits 1 on any failure.

  python3 pipeline/search/test_search.py --db search/library.sqlite

Checks the v32 citation layer (verse, concept, death-year, collation-level filters and their output fields),
and that the older features still work (root search, by-author, hadith join). Needs an index that includes
the Qur'an (sample builds: --only 0001Quran,...).
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(db, *args):
    out = subprocess.run([sys.executable, os.path.join(HERE, "search.py"), "--db", db, *args], capture_output=True, text=True)
    return out.returncode, out.stdout, out.stderr


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--db", default="search/library.sqlite"); a = ap.parse_args()
    fails = []
    def check(name, cond, detail=""):
        print(("ok    " if cond else "FAIL  ") + name + (f"  ({detail})" if detail and not cond else ""))
        if not cond: fails.append(name)

    rc, out, err = run(a.db, "--verse", "2:31", "--chrono", "--json", "--limit", "200")
    hits = json.loads(out)["hits"] if rc == 0 else []
    check("verse 2:31 returns the verse itself first", hits and hits[0]["uid"] == "urn:quran:2:31", err[:200])
    d = [h["death_ah"] for h in hits if h["death_ah"] is not None]
    check("--chrono orders by death year", d == sorted(d))
    check("hits carry verse_how, loc, death_ah", hits and all("verse_how" in h and "loc" in h for h in hits) and len(d) >= 1)

    rc, out, _ = run(a.db, "--verse", "2:31", "--how", "verse", "--json")
    check("--how verse gives exactly the verse", rc == 0 and json.loads(out)["total"] == 1)

    rc, out, _ = run(a.db, "--root", "وجد", "--min-level", "corroborated", "--json", "--limit", "500")
    hs = json.loads(out)["hits"] if rc == 0 else []
    typed = ("ganjoor", "openiti", "shamela", "typed")
    check("--min-level keeps typed text and only corroborated/verified OCR",
          rc == 0 and all(h["source_type"] in typed or h["ocr_level"] in ("corroborated", "verified") for h in hs))

    rc, out, _ = run(a.db, "--root", "نور", "--before", "400", "--json", "--limit", "500")
    hs = json.loads(out)["hits"] if rc == 0 else []
    check("--before 400 only returns authors d. <= 400", rc == 0 and hs and all(h["death_ah"] is not None and h["death_ah"] <= 400 for h in hs))

    rc, _, err = run(a.db, "--concept", "no_such_concept")
    check("unknown concept lists the known ones", rc != 0 and "qutb" in err)
    rc, out, _ = run(a.db, "--concept", "qutb", "--json")
    check("--concept qutb runs", rc == 0 and "total" in json.loads(out))

    rc, out, _ = run(a.db, "--root", "نور", "--by-author", "--chrono", "--json")
    check("--by-author carries death_ah", rc == 0 and all("death_ah" in r for r in json.loads(out)))

    rc, out, _ = run(a.db, "إنما الأعمال بالنيات", "--limit", "3")
    check("plain surface search still works", rc == 0 and "matching units" in out)

    print("\n" + ("all passed" if not fails else f"{len(fails)} failed: " + "; ".join(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
