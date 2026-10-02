#!/usr/bin/env python3
"""
build_sayings.py - v44: the critics' entries on current sayings, as one table.

Four classical works are built as numbered entries, "saying, then what is known of it". Most of these sayings are
not in the hadith collections at all, so they cannot be joined to the hadith layer; they get a table of their own.

  al-Dhahabi (d. 748), Talkhis al-Mawdu'at     his summary of Ibn al-Jawzi's fabricated reports, with his own verdicts
  al-Sakhawi (d. 902), al-Maqasid al-hasana    sayings current on people's tongues
  Mulla 'Ali al-Qari (d. 1014), al-Asrar al-marfu'a   fabricated and baseless sayings
  al-'Ajluni (d. 1162), Kashf al-khafa'        the largest collection of current sayings (v45)
Modern, in its own file (apparatus/sayings/sayings_modern.tsv.gz), never merged: al-Albani's verdict on each hadith
of al-Jami' al-saghir (v45).

Output: apparatus/sayings/sayings.tsv.gz, one row per entry:
  saying_id      urn:saying:<work>:<entry number>
  group          the same saying in another of the three works (S00001 ...), matched by loose wording
  critic, death_ah, work, entry
  saying         the saying as the critic words it
  verdict        what he says of it, in his words (the paragraphs of the entry, up to 900 characters)
  cues           verdict words found in it, in the order they occur: fabricated | no_basis | not_prophetic |
                 not_found | weak | fair | sound | mutawatir | cross_reference. A cue is a pointer, not a ruling: the
                 same entry may say "its chain is weak but its meaning is sound". Quote `verdict`, never `cues`.
  record, loc    the record id to cite and its volume:page
  hadith_ids     hadith of the layer with this wording (up to 5), when it IS in the collections

Ibn al-Jawzi's Mawdu'at and al-Suyuti's La'ali are not entered here: they give each report with its full chains and
no entry numbering, so authenticate.py searches them as text.

Usage: python3 pipeline/hadith/build_sayings.py [--repo .]
"""
import argparse, collections, csv, gzip, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "search"))
from textnorm import norm  # noqa: E402
from build_critic_grades import J, raw_of, clean, Layer, toks, shingles  # noqa: E402

CUES = [("fabricated", r"موضوع|مكذوب|مختلق|كذب|باطل|من وضع"),
        ("no_basis", r"لا اصل له|ليس له اصل|لا يعرف له اصل|لا اصل لها|لم يوجد"),
        ("not_prophetic", r"ليس بحديث|ليس من كلام النبي|ليس من كلام رسول|من كلام|لا يعرف مرفوعا|من قول|موقوف"),
        ("not_found", r"لم اقف عليه|لا اعرفه|لم اجده|لم اره|لم اقف له"),
        ("weak", r"ضعيف|لا يصح|لا يثبت|ليس بثابت|منكر|واه|غريب|فيه مقال|لين"),
        ("fair", r"حسن|جيد"), ("sound", r"صحيح|متفق عليه|ثابت"), ("mutawatir", r"متواتر")]
CUES = [(k, re.compile(r"(?<![ء-ي])[وف]?(?:ال)?(?:" + p + r")(?![ء-ي])")) for k, p in CUES]
COLS = ["saying_id", "group", "critic", "death_ah", "work", "entry", "saying", "verdict", "cues", "record", "loc", "hadith_ids"]


def cues(text):
    n = norm(text); found = []
    for k, p in CUES:
        m = p.search(n)
        if m: found.append((m.start(), k))
    return " ".join(k for _, k in sorted(found))


def loc(r):
    pb = r.get("page_before")
    return f"{r.get('vol')}:{pb + 1}" if isinstance(pb, int) else ""


def entries(repo):
    # al-Sakhawi: "125 حديث ( saying ) rest", then paragraphs until the next entry
    recs = list(J(os.path.join(repo, "corpus/grading/0902Sakhawi.MaqasidHasana.jsonl.gz")))
    HEAD = re.compile(r"^(\d+)\s+حديث\s*\(\s*(.+?)\s*\)\s*(.*)$", re.S)
    cur = None
    for r in recs:
        t = clean(raw_of(r)); m = HEAD.match(t)
        if m:
            if cur: yield cur
            cur = dict(critic="al-Sakhawi", death_ah=902, work="al-Maqasid al-hasana", key="0902Sakhawi.MaqasidHasana",
                       entry=m.group(1), saying=m.group(2), verdict=m.group(3), record=r["id"], loc=loc(r))
        elif cur and t and r.get("kind") != "heading" and len(cur["verdict"]) < 900:
            cur["verdict"] = (cur["verdict"] + " " + t).strip()
    if cur: yield cur
    # al-Qari: "17 حديث" alone, then "saying + verdict +", then more paragraphs
    recs = list(J(os.path.join(repo, "corpus/wilaya/1014MullaCaliQari.AsrarMarfuca.jsonl.gz")))
    cur = None; want = None
    for r in recs:
        t = clean(raw_of(r)); m = re.match(r"^(\d+)\s+حديث\s*$", t)
        if m:
            if cur: yield cur
            cur = None; want = m.group(1); continue
        if want and t:
            parts = [p.strip() for p in t.split("+")]
            cur = dict(critic="Mulla ʿAli al-Qari", death_ah=1014, work="al-Asrar al-marfuʿa", key="1014MullaCaliQari.AsrarMarfuca",
                       entry=want, saying=parts[0], verdict=" ".join(p for p in parts[1:] if p), record=r["id"], loc=loc(r))
            want = None
        elif cur and t and r.get("kind") != "heading" and len(cur["verdict"]) < 900:
            cur["verdict"] = (cur["verdict"] + " " + t.replace("+", " ")).strip()
    if cur: yield cur
    # al-'Ajluni (v45): "362 ( saying ) what is known of it", then paragraphs until the next entry
    p = os.path.join(repo, "corpus/mawduat/1162IbnMuammadAbuFidaCajluni.KashfKhafa.jsonl.gz")
    if os.path.exists(p):
        HEADA = re.compile(r"^(\d+)\s*\(\s*(.+?)\s*\)\s*(.*)$", re.S); cur = None
        for r in J(p):
            t = clean(raw_of(r)); m = HEADA.match(t)
            if m:
                if cur: yield cur
                cur = dict(critic="al-ʿAjluni", death_ah=1162, work="Kashf al-khafaʾ", key="1162Cajluni.KashfKhafa",
                           entry=m.group(1), saying=m.group(2), verdict=m.group(3), record=r["id"], loc=loc(r))
            elif cur and t and r.get("kind") != "heading" and len(cur["verdict"]) < 900:
                cur["verdict"] = (cur["verdict"] + " " + t).strip()
        if cur: yield cur
    # al-Dhahabi: heading "### | 110 -", then 'حديث: " saying ". verdict'
    recs = list(J(os.path.join(repo, "corpus/grading/0748Dhahabi.TalkhisMawducatIbnJawzi.jsonl.gz")))
    no = None
    for r in recs:
        raw = raw_of(r)
        if r.get("kind") == "heading":
            m = re.search(r"(\d+)\s*-", raw); no = m.group(1) if m else None; continue
        t = clean(raw); m = re.match(r'^(?:و)?حديث\s*:?\s*["«(]+\s*(.+?)\s*["»)]+\s*[.،:]?\s*(.*)$', t, re.S)
        if no and m:
            yield dict(critic="al-Dhahabi", death_ah=748, work="Talkhis al-Mawduʿat", key="0748Dhahabi.TalkhisMawducat",
                       entry=no, saying=m.group(1), verdict=m.group(2), record=r["id"], loc=loc(r))
            no = None


def modern(repo):
    """v45, MODERN, its own file: al-Albani's verdict on each hadith of al-Jami' al-saghir and its supplement.
    The text runs: heading "### | 501 -", the hadith, its sources, heading "[حكم الألباني]", his verdict."""
    p = os.path.join(repo, "corpus/modern/0911Suyuti.SahihWaDacif.jsonl.gz")
    if not os.path.exists(p): return 0
    rows = []; no = None; body = []; want = False
    for r in J(p):
        raw = raw_of(r)
        if r.get("kind") == "heading":
            if "حكم الألباني" in raw: want = True; continue
            m = re.search(r"(\d+)\s*-", raw)
            if m: no, body, want = m.group(1), [], False
            continue
        t = clean(raw)
        if not t or not no: continue
        if want:
            rows.append(["urn:saying:1420Albani.SahihWaDacifJamic:" + no, "al-Albani", 1420, "Sahih wa-daʿif al-Jamiʿ al-saghir", no,
                         (body[0] if body else "")[:400], t[:300], r["id"], " ".join(body[1:2])[:200]])
            no = None; want = False
        else: body.append(t)
    out = os.path.join(repo, "apparatus/sayings/sayings_modern.tsv.gz"); os.makedirs(os.path.dirname(out), exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["saying_id", "critic", "death_ah", "work", "entry", "saying", "verdict", "record", "sources_named"])
        w.writerows(rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="."); a = ap.parse_args()
    E = list(entries(a.repo))
    for e in E:
        e["saying"] = e["saying"].strip(" .")[:400]; e["verdict"] = e["verdict"][:900]
        e["saying_id"] = f"urn:saying:{e['key']}:{e['entry']}"
        c = cues(e["verdict"])
        if not c and re.match(r"^\s*في\s+\S+(?:\s+\S+){0,4}\s*$", e["verdict"]): c = "cross_reference"
        e["cues"] = c
    # the same saying in another work: word-set overlap (Jaccard >= 0.6), grouped
    sets = [set(toks(e["saying"])) for e in E]
    inv = collections.defaultdict(list)
    for i, s in enumerate(sets):
        for w in s: inv[w].append(i)
    parent = list(range(len(E)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i, s in enumerate(sets):
        if len(s) < 3: continue
        votes = collections.Counter()
        for w in s:
            if len(inv[w]) < 400:
                for j in inv[w]:
                    if j > i: votes[j] += 1
        for j, v in votes.items():
            if E[j]["key"] != E[i]["key"] and v / len(s | sets[j]) >= 0.6: parent[find(i)] = find(j)
    members = collections.defaultdict(list)
    for i in range(len(E)): members[find(i)].append(i)
    gid = 0
    for root, ids in sorted(members.items(), key=lambda kv: min(kv[1])):
        if len(ids) > 1:
            gid += 1
            for i in ids: E[i]["group"] = f"S{gid:05d}"
    # is the wording in the collections?
    cols = sorted(p[:-9] for p in os.listdir(os.path.join(a.repo, "apparatus/hadith")) if p.endswith(".jsonl.gz"))
    L = Layer(a.repo, cols, "matn"); found = 0
    for e in E:
        c = L.match(e["saying"], thr=0.7, min_hits=3)
        e["hadith_ids"] = ";".join(h["id"] for _, h in sorted(c, key=lambda x: -x[0])[:5]); found += bool(c)
    modern_n = modern(a.repo)
    out = os.path.join(a.repo, "apparatus/sayings/sayings.tsv.gz"); os.makedirs(os.path.dirname(out), exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(COLS)
        for e in E: w.writerow([e.get(k, "") for k in COLS])
    summary = {"entries": len(E), "modern_entries_albani_jami": modern_n, "by_work": dict(collections.Counter(e["work"] for e in E)),
               "groups_across_works": gid, "entries_in_a_group": sum(1 for e in E if e.get("group")),
               "entries_with_wording_in_the_collections": found,
               "cue_first": dict(collections.Counter((e["cues"].split() or ["none"])[0] for e in E).most_common())}
    sp = os.path.join(a.repo, "catalogs/critic_grades_summary.json")
    S = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    S["sayings"] = summary; json.dump(S, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
