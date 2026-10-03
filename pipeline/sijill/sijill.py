#!/usr/bin/env python3
"""
sijill.py - v41: the record (sijill) of the digital Jalasa: what our studies conclude when claims are tested against
the Qur'an, the Sunna, the Companions and the masters, kept as a growing web of entries.

Design (docs/sijill/README.md):
  - Everything is an entry: one JSON object per line in sijill/entries/*.jsonl, append-only. Fields:
      id (type:slug), type, schema (1), date, status (draft | reviewed | superseded), title, text, data {...},
      links [{rel, to, note}], cites [{record, loc, quote, level}], by
  - Types and relations are open registries (sijill/registry/types.tsv, relations.tsv): a new kind of thing or link
    is one new row; nothing recorded before has to change.
  - Nothing is overwritten: a correction is a new entry that links {rel: supersedes, to: old id}.
  - Strict only where it matters: ids unique, types and relations registered, links point to existing entries,
    and every cited record id resolves in the library (corpus, hadith layer, Qur'an). Everything else is open.
  - Views are generated, never edited: sijill/views/*.md (questions with their positions in chronological order,
    voices and where they agree or differ, open questions).
Usage: python3 pipeline/sijill/sijill.py --repo . validate | views | all
"""
import argparse, collections, csv, glob, gzip, json, os, re, sys

STANCE = {"affirms": "affirms", "qualifies": "qualifies", "rejects": "rejects"}


def load(repo):
    ents, errs = [], []
    for p in sorted(glob.glob(os.path.join(repo, "sijill/entries/*.jsonl"))):
        for i, l in enumerate(open(p, encoding="utf-8"), 1):
            if not l.strip(): continue
            try: e = json.loads(l); e["_where"] = f"{os.path.basename(p)}:{i}"; ents.append(e)
            except Exception as x: errs.append(f"{os.path.basename(p)}:{i}: not JSON ({x})")
    return ents, errs


def registry(repo, name):
    return {r[next(iter(r))] for r in csv.DictReader(open(os.path.join(repo, f"sijill/registry/{name}.tsv"), encoding="utf-8"), delimiter="\t")}


def resolve(repo, records):
    """which cited record ids exist in the library; only the files a cited id points to are opened."""
    found, want = set(), collections.defaultdict(set)
    for r in records:
        if r.startswith("urn:quran:"):
            m = re.fullmatch(r"urn:quran:(\d+):(\d+)", r)
            if m and 1 <= int(m.group(1)) <= 114: want["corpus/quran/*"].add(r)
        elif r.startswith("urn:hadith:"):
            want[f"apparatus/hadith/{r.split(':')[2]}.jsonl.gz"].add(r)
        elif r.startswith("urn:openiti:"):
            work = ".".join(r.split(":")[2].split(".")[:2]); want[f"corpus/**/*{work}*.jsonl*"].add(r)
        elif r.startswith("urn:lib:"):
            key = r.split(":")[2]; fo, book = key.split(".", 1); want[f"corpus/{fo}/{book}*.jsonl*"].add(r)
        elif r.startswith("urn:sufi:rumi.mathnawi:"):
            want["corpus/mathnawi/full/*.jsonl"].add(r)
        else: want["corpus/**/*.jsonl*"].add(r)
    for pat, ids in want.items():
        for p in glob.glob(os.path.join(repo, pat), recursive=True):
            if not re.search(r"\.jsonl(\.gz)?$", p): continue
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt", encoding="utf-8") as f:
                for l in f:
                    if '"id"' not in l: continue
                    m = re.search(r'"id":\s*"([^"]+)"', l)
                    if m and m.group(1) in ids: found.add(m.group(1))
    return found


def validate(repo):
    ents, errs = load(repo)
    types, rels = registry(repo, "types"), registry(repo, "relations")
    ids = collections.Counter(e.get("id") for e in ents)
    errs += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    cited = set()
    for e in ents:
        w = e.get("_where")
        for k in ("id", "type", "status"):
            if not e.get(k): errs.append(f"{w}: missing {k}")
        if e.get("type") and e["type"] not in types: errs.append(f"{w}: type '{e['type']}' not in registry/types.tsv")
        if e.get("id") and e.get("type") and not e["id"].startswith(e["type"] + ":"): errs.append(f"{w}: id should start with '{e['type']}:'")
        for ln in e.get("links", []):
            if ln.get("rel") not in rels: errs.append(f"{w}: relation '{ln.get('rel')}' not in registry/relations.tsv")
            if ln.get("to") not in ids: errs.append(f"{w}: link to unknown entry {ln.get('to')}")
        for c in e.get("cites", []):
            if c.get("record"): cited.add(c["record"])
    found = resolve(repo, cited)
    missing = sorted(cited - found)
    errs += [f"cited record not in the library: {r}" for r in missing]
    print(f"{len(ents)} entries, {len(cited)} cited records ({len(found)} resolved); {len(errs)} problems")
    for x in errs: print("  ", x)
    return not errs


def views(repo):
    ents, _ = load(repo)
    E = {e["id"]: e for e in ents if e.get("status") != "superseded"}
    sup = {ln["to"] for e in ents for ln in e.get("links", []) if ln.get("rel") == "supersedes"}
    E = {k: v for k, v in E.items() if k not in sup}
    death = lambda vid: (E.get(vid, {}).get("data", {}).get("death_ah") if isinstance(E.get(vid, {}).get("data", {}).get("death_ah"), int) else 9999)
    def cite_s(e):
        return "; ".join(f"`{c['record']}`" + (f" ({c['loc']})" if c.get("loc") else "") if c.get("record") else c.get("loc", "") for c in e.get("cites", []))
    out = os.path.join(repo, "sijill/views"); os.makedirs(out, exist_ok=True)
    # 1. inferences with their positions, oldest voice first
    L = ["# Inferences and where the voices stand", "", "_Generated by pipeline/sijill/sijill.py from sijill/entries; do not edit._", ""]
    pos_by = collections.defaultdict(list)
    for e in E.values():
        if e["type"] != "position": continue
        voice = next((ln["to"] for ln in e.get("links", []) if ln["rel"] == "held_by"), None)
        for ln in e.get("links", []):
            if ln["rel"] in STANCE: pos_by[ln["to"]].append((death(voice), voice, ln["rel"], e))
    for inf in sorted((e for e in E.values() if e["type"] in ("inference", "question")), key=lambda e: e["id"]):
        verdict = next((v for v in E.values() if v["type"] == "verdict" and any(ln["to"] == inf["id"] for ln in v.get("links", []))), None)
        L += [f"## {inf.get('title', inf['id'])}", "", inf.get("text", ""), ""]
        if verdict: L += [f"**Verdict: {verdict.get('data', {}).get('verdict', '?')}** ({verdict['status']}). {verdict.get('text', '')}", ""]
        for d, voice, stance, e in sorted(pos_by.get(inf["id"], []), key=lambda x: x[0]):
            v = E.get(voice, {}); dd = v.get("data", {}).get("death_ah")
            L.append(f"- **{v.get('title', voice)}**{f' (d. {dd} AH)' if isinstance(dd, int) else ''}: *{stance}*. {e.get('text', '')} {cite_s(e)}")
        L.append("")
    open(os.path.join(out, "inferences.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    # 2. voices: who sides with whom
    stances = collections.defaultdict(dict)
    for target, ps in pos_by.items():
        for d, voice, stance, e in ps: stances[voice][target] = stance
    V = ["# Voices: agreement and difference", "",
         "_Generated. For each pair of voices with positions on the same inferences: same stance = agree; affirms vs rejects = differ;",
         "anything involving 'qualifies' = partly. Counts are over the inferences both addressed._", "",
         "| voice | d. AH | positions | agrees | partly | differs |", "|---|---|---|---|---|---|"]
    name = lambda o: E.get(o, {}).get("title", o)
    for vid in sorted(stances, key=death):
        cols = {"agree": [], "partly": [], "differ": []}
        for o in sorted(stances, key=death):
            if o == vid: continue
            common = set(stances[vid]) & set(stances[o])
            if not common: continue
            k = collections.Counter("agree" if stances[vid][t] == stances[o][t] else
                                    "differ" if {stances[vid][t], stances[o][t]} == {"affirms", "rejects"} else "partly" for t in common)
            for kind, c in k.items(): cols[kind].append(f"{name(o)} ({c}/{len(common)})")
        dd = E.get(vid, {}).get("data", {}).get("death_ah", "")
        V.append(f"| {name(vid)} | {dd if dd is not None else 'living'} | {len(stances[vid])} | " + " | ".join(", ".join(cols[c]) for c in ("agree", "partly", "differ")) + " |")
    open(os.path.join(out, "voices.md"), "w", encoding="utf-8").write("\n".join(V) + "\n")
    # 3. open questions
    O = ["# Open questions", "", "_Generated; what the studies could not settle, and what would settle it._", ""]
    answered = collections.defaultdict(list)          # v53: an entry that links {rel: answers} to an open question closes it
    for e in E.values():
        for ln in e.get("links", []):
            if ln.get("rel") == "answers": answered[ln["to"]].append(e)
    A = []
    for e in sorted((e for e in E.values() if e["type"] == "open_question"), key=lambda e: e["id"]):
        if e["id"] in answered:
            A.append(f"- **{e.get('title', e['id'])}** Answered by " + "; ".join(f"`{x['id']}`: {x.get('text', '')}" for x in answered[e["id"]]))
            continue
        O.append(f"- **{e.get('title', e['id'])}** ({e['status']}). {e.get('text', '')}" + (f" Needs: {e['data']['needs']}" if e.get("data", {}).get("needs") else ""))
    if A: O += ["", "## Answered", ""] + A
    open(os.path.join(out, "open_questions.md"), "w", encoding="utf-8").write("\n".join(O) + "\n")
    print("views written: sijill/views/inferences.md, voices.md, open_questions.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); ap.add_argument("cmd", choices=["validate", "views", "all"])
    a = ap.parse_args()
    ok = True
    if a.cmd in ("validate", "all"): ok = validate(a.repo)
    if a.cmd in ("views", "all"): views(a.repo)
    sys.exit(0 if ok else 1)
