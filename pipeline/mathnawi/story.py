#!/usr/bin/env python3
"""
story.py - v54: a Mathnawi couplet with its story. A couplet is never quoted bare: this prints the section it stands
in with Rumi's own heading, the story the section belongs to (Book 1; Claude's reading of the headings), whether the
section is the tale, a return to it or Rumi's commentary, and the readings already recorded for it in the sijill.

  python3 pipeline/mathnawi/story.py 1:263                      # book:couplet in Nicholson's numbering
  python3 pipeline/mathnawi/story.py urn:sufi:rumi.mathnawi:4.b3692 --show 2      # with two couplets either side
  python3 pipeline/mathnawi/story.py --stories 1                # the story map of a book
  python3 pipeline/mathnawi/story.py --headings 1 --from 84 --to 96             # Rumi's headings, section by section
Reads apparatus/mathnawi/sections.tsv (build_sections.py), apparatus/mathnawi/stories_book1.tsv, corpus/mathnawi and
sijill/entries. The voice (who speaks: the narrator, a character, Rumi himself) is recorded per passage in the sijill
as it is read; the corpus files do not carry it yet.
"""
import argparse, csv, glob, json, os, re, sys


def rows(repo, rel):
    p = os.path.join(repo, rel)
    if not os.path.exists(p): return []
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))


def couplets(repo, book):
    return rows(repo, f"corpus/mathnawi/book{book}.tsv")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("couplet", nargs="?", help="book:number (Nicholson) or a couplet id")
    ap.add_argument("--repo", default="."); ap.add_argument("--show", type=int, default=0, help="couplets of context either side")
    ap.add_argument("--stories", type=int, metavar="BOOK"); ap.add_argument("--headings", type=int, metavar="BOOK")
    ap.add_argument("--from", dest="lo", type=int, default=1); ap.add_argument("--to", dest="hi", type=int, default=10 ** 6)
    a = ap.parse_args()
    secs = rows(a.repo, "apparatus/mathnawi/sections.tsv")
    if not secs: sys.exit("apparatus/mathnawi/sections.tsv is missing: run pipeline/mathnawi/build_sections.py")
    if a.stories:
        st = rows(a.repo, f"apparatus/mathnawi/stories_book{a.stories}.tsv")
        if not st: sys.exit(f"no story map for book {a.stories} yet (only Rumi's headings: --headings {a.stories})")
        for s in st:
            print(f"{s['story']:>3}. {s['title_en']}  [{a.stories}:{s['first_nicholson']}-{s['last_nicholson']}; sections {s['first_section']}-{s['last_section']}]")
            if s["inset_tales"]: print(f"       inset: {s['inset_tales']}")
        print(f"\n({st[0]['status']})"); return
    if a.headings:
        for s in secs:
            if int(s["book"]) == a.headings and a.lo <= int(s["section"]) <= a.hi:
                print(f"{s['section']:>4} [{s['kind']:<10}] {a.headings}:{s['first_nicholson']}-{s['last_nicholson']}  {s['heading']}")
        return
    if not a.couplet: ap.error("give a couplet (book:number or id), or --stories BOOK, or --headings BOOK")
    m = re.fullmatch(r"(\d):(\d+[a-z]?)", a.couplet) or re.fullmatch(r"urn:sufi:rumi\.mathnawi:(\d)\.[bg](\d+[a-z]?)", a.couplet)
    if not m: sys.exit("not a couplet: use book:number, e.g. 1:263, or urn:sufi:rumi.mathnawi:1.b0263")
    book = int(m.group(1)); cs = couplets(a.repo, book)
    want = a.couplet if a.couplet.startswith("urn:") else None
    num = m.group(2).lstrip("0")
    i = next((k for k, r in enumerate(cs) if (r["id"] == want if want else r["id"].split(".b")[-1].lstrip("0") == num)), None)
    if i is None: sys.exit(f"couplet not found in book {book}")
    r = cs[i]; s = next(x for x in secs if int(x["book"]) == book and x["section"] == r["section"])
    kinds = {"tale": "opens a tale", "return": "returns to a tale left off", "exposition": "Rumi comments or explains", "step": "a step in the telling"}
    print(f"{r['id']}   Mathnawi {book}:{r['id'].split('.b')[-1].lstrip('0')}")
    print(f"  {r['hemistich_1']} / {r['hemistich_2']}")
    print(f"section {s['section']} of book {book} ({book}:{s['first_nicholson']}-{s['last_nicholson']}, {s['couplets']} couplets); the heading {kinds.get(s['kind'], s['kind'])} (derived from its first words)")
    print(f"  Rumi's heading: {s['heading']}")
    for t in rows(a.repo, f"apparatus/mathnawi/stories_book{book}.tsv"):
        if int(t["first_section"]) <= int(s["section"]) <= int(t["last_section"]):
            print(f"story {t['story']} of book {book}: {t['title_en']} ({book}:{t['first_nicholson']}-{t['last_nicholson']})  [{t['status']}]")
            if t["inset_tales"]: print(f"  inset tales: {t['inset_tales']}")
            if t["note"]: print(f"  note: {t['note']}")
    pos = {x["id"]: k for k, x in enumerate(cs)}; found = []; ents = {}
    for p in sorted(glob.glob(os.path.join(a.repo, "sijill/entries/*.jsonl"))):
        for l in open(p, encoding="utf-8"):
            if l.strip():
                try: e = json.loads(l); ents[e["id"]] = e
                except ValueError: pass
    for e in ents.values():
        if e.get("type") != "passage": continue
        ids = [c["record"] for c in e.get("cites", []) if c.get("record") in pos]
        if ids and pos[ids[0]] <= i <= pos[ids[-1]]: found.append(e)
    for e in sorted(found, key=lambda e: e.get("data", {}).get("order", 0)):
        rd = [x for x in ents.values() if x.get("type") == "reading" and any(ln["rel"] == "reads" and ln["to"] == e["id"] for ln in x.get("links", []))]
        lay = ", ".join(sorted({x["data"].get("layer", "?") for x in rd}))
        print(f"sijill: {e['id']}  {e['data'].get('locator', '')}; voice in the text: {e['data'].get('voice_in_text', '?')}; {len(rd)} readings ({lay or 'none yet'})")
    if not found: print("sijill: no passage recorded for this couplet yet; if you quote it, say who speaks and whose reading you give")
    else: print("  the readings are set out in sijill/views/readings.md")
    if a.show:
        print()
        for x in cs[max(0, i - a.show): i + a.show + 1]:
            print(f"  {'>' if x is r else ' '} {x['id'].split('.b')[-1].lstrip('0'):>5}  {x['hemistich_1']} / {x['hemistich_2']}")


if __name__ == "__main__":
    import signal; signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
