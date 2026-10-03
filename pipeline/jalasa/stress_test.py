#!/usr/bin/env python3
"""
stress_test.py - v50: runs the stress test written in docs/jalasa/STRESS_TEST.md.

The DOCUMENT is the test. Every table row in it whose first cell is a case id (A1, B3 ...) is one case:

  | id | level | check | input | where | expect | why |

This script reads those rows, runs the repo's own tools on them, and writes a scorecard. To add, change or retire a
case, edit the document: no code changes. To add a new KIND of check, add a function here and register it in CHECKS.

  level   must = the repo already does this; a failure is a regression (the script exits 1)
          goal = the Jalasa needs this and the repo does not do it yet; tracked, never fails the run.
                 When a goal starts passing, the report says so: change it to must in the document.
  check   authenticate | same | search | verse | concept | caliph | cite | sijill | metric | time | crash
  expect  conditions joined by commas, all must hold. Each check's vocabulary is listed in the document.

Usage:  python3 pipeline/jalasa/stress_test.py [--repo .] [--doc docs/jalasa/STRESS_TEST.md] [--only A,C] [--no-history]
Writes: reports/jalasa/STRESS_REPORT.md   the scorecard of this run
        reports/jalasa/stress_last.json   the same as data
        reports/jalasa/stress_history.tsv one line per run (date, commit, passes), so progress shows over time
Standard library only. About two to four minutes.
"""
import argparse, collections, csv, datetime, glob, gzip, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "search"))
from textnorm import norm  # noqa: E402

ROW = re.compile(r"^\|\s*([A-Z]\d+)\s*\|")
CMP = re.compile(r"^([a-z_]+)\s*(>=|<=|==|>|<)\s*([0-9.]+)\s*(s|%)?$")
LETTERS = re.compile(r"[^ء-ي ]+")


def plain(t):
    return " ".join(LETTERS.sub(" ", norm(t or "")).split())


def read_cases(path):
    cases, section = [], ""
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "): section = line[3:].strip()
        if not ROW.match(line): continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) < 7: sys.exit(f"case row needs 7 cells: {line.strip()[:80]}")
        cid, level, check, inp, where, expect, why = cells[:7]
        if level not in ("must", "goal"): sys.exit(f"{cid}: level must be 'must' or 'goal', not {level!r}")
        cases.append({"id": cid, "level": level, "check": check, "input": inp, "where": where, "expect": expect, "why": why,
                      "section": section})
    ids = [c["id"] for c in cases]
    dup = [i for i, n in collections.Counter(ids).items() if n > 1]
    if dup: sys.exit(f"duplicate case ids: {dup}")
    return cases


def run(cmd, repo, timeout=1500):
    t = time.time()
    p = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr, time.time() - t


def compare(found, expect):
    """expect 'records>=3, works>=2' against found {'records': 5, 'works': 1} -> (ok, [failed conditions])"""
    bad = []
    for cond in [c.strip() for c in expect.split(",") if c.strip()]:
        m = CMP.match(cond)
        if not m: bad.append(f"cannot read condition {cond!r}"); continue
        k, op, v, unit = m.group(1), m.group(2), float(m.group(3)), m.group(4)
        if k not in found: bad.append(f"{k} not measured"); continue
        x = found[k] * (100 if unit == "%" else 1)
        if not {">=": x >= v, "<=": x <= v, "==": x == v, ">": x > v, "<": x < v}[op]: bad.append(f"{cond} (found {round(x, 2)})")
    return not bad, bad


# ---------- one batched run of each tool ----------
class Tools:
    def __init__(self, repo, cases):
        self.repo, self.timing, self.notes = repo, {}, []
        say = []
        for c in cases:
            if c["check"] == "authenticate" or (c["check"] == "crash" and c["where"] == "authenticate"): say.append(c["input"])
            if c["check"] == "same": say += [x.strip() for x in c["input"].split("//")]
        self.sayings = list(dict.fromkeys(say)); self.auth = {}
        if self.sayings:
            rc, out, err, dt = run([sys.executable, "pipeline/hadith/authenticate.py", *self.sayings, "--json", "--limit", "100000"], repo)
            self.timing["authenticate_all"] = dt; self.timing["authenticate_per_saying"] = dt / len(self.sayings)
            self.auth_rc = rc
            if rc == 0:
                for s, r in zip(self.sayings, json.loads(out)): self.auth[s] = r
            else: self.notes.append("authenticate.py failed: " + err[-300:])
        groups = collections.defaultdict(list)
        for c in cases:
            if c["check"] == "search": groups[c["where"]].append(c["input"])
        self.search = {}
        for where, phrases in groups.items():
            phrases = list(dict.fromkeys(phrases))
            cmd = [sys.executable, "pipeline/search/textsearch.py", *phrases, "--count"] + (["--folder", where] if where and where != "all" else [])
            rc, out, err, dt = run(cmd, repo)
            if where in ("", "all"): self.timing["search_whole_corpus"] = dt
            blocks = re.split(r"\n=+\n", out)
            for b in blocks:
                m = re.search(r'"(.+?)": (\d+) records? in (\d+) works?', b)
                if not m: continue
                per = collections.Counter()
                for n, key in re.findall(r"^\s+(\d+)\s+(\S+)\s*$", b, re.M): per[key.split(".")[0]] += int(n)
                for ph in phrases:
                    if plain(ph) == plain(m.group(1)): self.search[(where, ph)] = {"records": int(m.group(2)), "works": int(m.group(3)), "per_folder": dict(per)}
            if rc != 0: self.notes.append(f"textsearch failed for {where}: {err[-200:]}")
        self._layer = None

    def layer(self):
        if self._layer is None:
            cal = collections.Counter(); n = 0
            for p in glob.glob(os.path.join(self.repo, "apparatus/hadith/*.jsonl.gz")):
                with gzip.open(p, "rt", encoding="utf-8") as fh:
                    for line in fh:
                        n += 1
                        m = re.search(r'"caliph": "([^"]+)"', line)
                        if m: cal[m.group(1)] += 1
            self._layer = {"hadith": n, "caliph": cal}
        return self._layer


# ---------- the checks: each returns (ok, what was found, in words) ----------
def c_authenticate(c, T):
    r = T.auth.get(c["input"])
    if r is None: return False, "the authenticate command did not run"
    H, K = r["hadith"], r["critics"]; bad = []; found = {"hadith": len(H), "critics": len(K), "entries": len(r.get("entries", [])),
                                                         "collections": len({e["collection"] for e in H})}
    for cond in [x.strip() for x in c["expect"].split(",") if x.strip()]:
        if cond.startswith("in:"):
            if not any(cond[3:].lower() in e["collection"].lower() for e in H): bad.append(cond)
        elif cond == "not_in_layer":
            if H: bad.append(f"not_in_layer (found {len(H)})")
        elif cond.startswith("critic:"):
            if not any(cond[7:].lower() in e["author"].lower() for e in K): bad.append(cond)
        elif cond.startswith("says:"):
            _, who, words = cond.split(":", 2); w = plain(words)
            if not any(who.lower() in e["author"].lower() and w in plain((e.get("text") or "") + " " + (e.get("then") or "")) for e in K): bad.append(cond)
        elif cond.startswith("grade:"):
            _, who, words = cond.split(":", 2); w = plain(words) or words.lower()
            if not any(who.lower() in g["by"].lower() and (w in plain(g["grade"]) or words.lower() in g["grade"].lower())
                       for e in H for g in e["grades_classical"]): bad.append(cond)
        elif cond == "modern_apart":
            mod = [g for e in H for g in e["grades_modern"]] + r.get("modern", [])
            leak = [g for e in H for g in e["grades_classical"] if re.search(r"Albani|Arna|Asad|Shakir", g["by"])] + \
                   [e for e in K if re.search(r"Albani|Shakir", e["author"])]
            if not mod or leak: bad.append(f"modern_apart (modern rows {len(mod)}, in the classical list {len(leak)})")
        elif cond == "cites":
            if not all(e.get("id") for e in K) or not all(e.get("id") for e in H): bad.append("cites (a hit without a record id)")
        else:
            ok, b = compare(found, cond); bad += b
    cols = ", ".join(sorted({e["collection"].split(",")[0] for e in H})[:6])
    return not bad, (f"{len(H)} hadith" + (f" ({cols})" if cols else "") + f", {len(K)} critic passages" + ("; FAILED: " + "; ".join(bad) if bad else ""))


def c_same(c, T):
    a, b = [x.strip() for x in c["input"].split("//")]
    ra, rb = T.auth.get(a), T.auth.get(b)
    if ra is None or rb is None: return False, "the authenticate command did not run"
    ia, ib = {e["id"] for e in ra["hadith"]}, {e["id"] for e in rb["hadith"]}
    ka, kb = {e["id"] for e in ra["critics"]}, {e["id"] for e in rb["critics"]}
    ok = ia == ib and ka == kb and (ia or ka)
    return bool(ok), f"first: {len(ia)} hadith, {len(ka)} passages; second: {len(ib)} hadith, {len(kb)} passages" + ("" if ok else "; they differ")


def c_search(c, T):
    f = T.search.get((c["where"], c["input"]))
    if f is None: return False, "no result came back for this phrase"
    found = dict(f); want = [x for x in c["where"].split(",") if x] if c["where"] not in ("", "all") else []
    found["folders_with_hits"] = sum(1 for w in want if f["per_folder"].get(w, 0) > 0); found["folders"] = len(want)
    exp = c["expect"].replace("each_folder", f"folders_with_hits>={len(want)}")
    ok, bad = compare(found, exp)
    per = ", ".join(f"{k} {v}" for k, v in sorted(f["per_folder"].items()))
    return ok, f"{f['records']} records in {f['works']} works" + (f" ({per})" if per else "") + ("; FAILED: " + "; ".join(bad) if bad else "")


def c_lookup(kind):
    def fn(c, T):
        rc, out, err, dt = run([sys.executable, "pipeline/index/lookup.py", "--repo", ".", "--" + kind, c["input"], "--per-work", "1", "--chars", "40"], T.repo)
        m = re.search(r"(\d+) passages in (\d+) works", out)
        if rc != 0 or not m: return False, "the lookup returned nothing" + (": " + err[-120:] if err else "")
        found = {"passages": int(m.group(1)), "works": int(m.group(2))}
        years = [int(y) for y in re.findall(r"\(d\. (\d+) AH", out)]
        found["oldest_first"] = int(years == sorted(years))
        ok, bad = compare(found, c["expect"])
        return ok, f"{found['passages']} passages in {found['works']} works" + ("; FAILED: " + "; ".join(bad) if bad else "")
    return fn


def c_caliph(c, T):
    n = T.layer()["caliph"].get(c["input"], 0)
    ok, bad = compare({"hadith": n}, c["expect"])
    return ok, f"{n} hadith reach {c['input']} in the layer" + ("; FAILED: " + "; ".join(bad) if bad else "")


def c_cite(c, T):
    rc, out, err, dt = run([sys.executable, "pipeline/search/cite.py", "--repo", ".", c["input"]] + ([c["where"]] if c["where"] else []), T.repo)
    ok = rc == 0 and bool(out.strip()) and "not found" not in out.lower()
    return ok, (out.strip().splitlines() or ["nothing"])[0][:140] if ok else "the record did not resolve: " + (out + err).strip()[-140:]


def c_story(c, T):
    """v54: a Mathnawi couplet comes back with Rumi's heading, its story and the readings recorded for it"""
    rc, out, err, dt = run([sys.executable, "pipeline/mathnawi/story.py", "--repo", ".", c["input"]], T.repo)
    if rc != 0: return False, "story.py failed: " + (out + err).strip()[-140:]
    found = {"heading": int("Rumi's heading:" in out), "story": int("\nstory " in out), "passages": len(re.findall(r"^sijill: passage:", out, re.M)),
             "readings": sum(int(n) for n in re.findall(r"; (\d+) readings", out))}
    ok, bad = compare(found, c["expect"])
    if c["where"] and c["where"] not in out: ok = False; bad = bad + [f"'{c['where']}' not in the output"]
    return ok, f"heading {'yes' if found['heading'] else 'no'}, story {'yes' if found['story'] else 'no'}, {found['passages']} passages, {found['readings']} readings" + ("; FAILED: " + "; ".join(bad) if bad else "")


def c_sijill(c, T):
    if c["input"] == "validator":
        rc, out, err, dt = run([sys.executable, "pipeline/sijill/sijill.py", "--repo", ".", "all"], T.repo)
        m = re.search(r"(\d+) entries.*?(\d+) problems", out)
        return rc == 0 and bool(m) and m.group(2) == "0", (m.group(0) if m else "the validator did not report")
    kind = c["input"].split(":", 1)[1]; n = 0
    for p in glob.glob(os.path.join(T.repo, "sijill/entries/*.jsonl")):
        for line in open(p, encoding="utf-8"):
            try: n += json.loads(line).get("type") == kind
            except ValueError: pass
    ok, bad = compare({"entries": n}, c["expect"])
    return ok, f"{n} entries of type {kind}" + ("; FAILED: " + "; ".join(bad) if bad else "")


def metrics(T):
    repo = T.repo; out = {}
    g = json.load(open(os.path.join(repo, "catalogs/critic_grades_summary.json"), encoding="utf-8")).get("coverage", {})
    if g.get("hadith"):
        out["share_no_classical_grade"] = g["no_classical_grade"] / g["hadith"]
        out["share_nothing_at_all"] = g["nothing_at_all"] / g["hadith"]
        if "no_grade_classical_or_modern" in g: out["share_no_grade_classical_or_modern"] = g["no_grade_classical_or_modern"] / g["hadith"]
        out["hadith"] = g["hadith"]; out["collections"] = g["collections"]
    l = json.load(open(os.path.join(repo, "catalogs/hadith_links_summary.json"), encoding="utf-8"))
    out["share_names_linked"] = l["share_linked"]; out["hadith_fully_linked"] = l["hadith_fully_linked"]; out["parallel_groups"] = l["parallels"]["groups"]
    with open(os.path.join(repo, "catalogs/works_index.tsv"), encoding="utf-8") as fh: out["works"] = sum(1 for _ in fh) - 1
    with open(os.path.join(repo, "catalogs/authentication_works.tsv"), encoding="utf-8") as fh: out["authentication_works"] = sum(1 for _ in fh) - 1
    out["dossiers"] = len(glob.glob(os.path.join(repo, "docs/dossiers/*.md")))
    return out


def c_metric(c, T):
    if not hasattr(T, "metrics"): T.metrics = metrics(T)
    k = c["input"]
    if k not in T.metrics: return False, f"no such measure: {k} (known: {', '.join(sorted(T.metrics))})"
    ok, bad = compare({"value": T.metrics[k]}, c["expect"])
    v = T.metrics[k]
    return ok, (f"{v:.1%}" if isinstance(v, float) and v <= 1 else str(v)) + ("; FAILED: " + "; ".join(bad) if bad else "")


def c_time(c, T):
    k = c["input"]
    if k not in T.timing: return False, f"not timed in this run: {k} (timed: {', '.join(sorted(T.timing))})"
    ok, bad = compare({"seconds": T.timing[k]}, c["expect"])
    return ok, f"{T.timing[k]:.0f} seconds" + ("; FAILED: " + "; ".join(bad) if bad else "")


def c_crash(c, T):
    if c["where"] == "authenticate":
        ok = c["input"] in T.auth
        return ok, "ran without error" if ok else "the command failed on this input"
    rc, out, err, dt = run([sys.executable, "pipeline/search/textsearch.py", c["input"], "--folder", c["where"] or "hadith", "--count"], T.repo)
    return rc == 0, "ran without error" if rc == 0 else "failed: " + err[-140:]


CHECKS = {"authenticate": c_authenticate, "same": c_same, "search": c_search, "verse": c_lookup("verse"), "concept": c_lookup("concept"),
          "caliph": c_caliph, "cite": c_cite, "story": c_story, "sijill": c_sijill, "metric": c_metric, "time": c_time, "crash": c_crash}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="."); ap.add_argument("--doc", default="docs/jalasa/STRESS_TEST.md")
    ap.add_argument("--only", default="", help="section letters to run, e.g. A,C"); ap.add_argument("--no-history", action="store_true")
    a = ap.parse_args(); repo = os.path.abspath(a.repo); t0 = time.time()
    cases = read_cases(os.path.join(repo, a.doc))
    if a.only: cases = [c for c in cases if c["id"][0] in a.only.split(",")]
    unknown = [c["id"] for c in cases if c["check"] not in CHECKS]
    if unknown: sys.exit(f"unknown check in cases {unknown}; known: {', '.join(CHECKS)}")
    T = Tools(repo, cases); results = []
    for c in cases:
        try: ok, found = CHECKS[c["check"]](c, T)
        except Exception as e:  # a broken case must not hide the others
            ok, found = False, f"the check itself failed: {type(e).__name__}: {e}"
        results.append({**c, "ok": bool(ok), "found": found})
    secs = time.time() - t0
    commit = subprocess.run(["git", "log", "-1", "--format=%h %s"], cwd=repo, capture_output=True, text=True).stdout.strip()
    today = datetime.date.today().isoformat()
    must = [r for r in results if r["level"] == "must"]; goal = [r for r in results if r["level"] == "goal"]
    mp, gp = sum(r["ok"] for r in must), sum(r["ok"] for r in goal)
    L = [f"# Jalasa stress test: scorecard", "",
         f"Run {today} on `{commit}` in {secs:.0f} seconds. Cases come from `{a.doc}`; edit that document to change them.", "",
         f"**Must: {mp} of {len(must)} pass.** These are things the repo already does; a failure is a regression.",
         f"**Goal: {gp} of {len(goal)} met.** These are things the Jalasa needs that the repo does not do yet.", "",
         "| Capability | Must | Goal met |", "|---|---|---|"]
    by = collections.OrderedDict()
    for r in results: by.setdefault(r["section"], []).append(r)
    for s, rs in by.items():
        m = [r for r in rs if r["level"] == "must"]; g = [r for r in rs if r["level"] == "goal"]
        L.append(f"| {s} | {sum(r['ok'] for r in m)} of {len(m)} | {sum(r['ok'] for r in g)} of {len(g)} |")
    def table(title, rows, intro):
        if not rows: return
        L.extend(["", f"## {title}", "", intro, "", "| Case | What it tests | Expected | Found |", "|---|---|---|---|"])
        for r in rows: L.append(f"| {r['id']} | {r['why']} | `{r['expect']}` | {r['found']} |")
    table("Regressions: a must that failed", [r for r in must if not r["ok"]], "Fix these before anything else.")
    table("Goals now met", [r for r in goal if r["ok"]], "Change these to `must` in the document so they are protected from now on.")
    table("Goals not yet met: the roadmap", [r for r in goal if not r["ok"]], "Each is a gap between the repo and what a Jalasa needs.")
    table("Passing", [r for r in must if r["ok"]], "")
    if T.notes: L.extend(["", "## Notes", ""] + [f"- {n}" for n in T.notes])
    L.extend(["", "## Timings", ""] + [f"- {k}: {v:.0f} seconds" for k, v in sorted(T.timing.items())])
    out_dir = os.path.join(repo, "reports/jalasa"); os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "STRESS_REPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump({"date": today, "commit": commit, "seconds": round(secs), "must": [mp, len(must)], "goal": [gp, len(goal)],
               "timing": {k: round(v, 1) for k, v in T.timing.items()},
               "results": [{k: r[k] for k in ("id", "level", "check", "section", "ok", "found")} for r in results]},
              open(os.path.join(out_dir, "stress_last.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not a.no_history and not a.only:
        hp = os.path.join(out_dir, "stress_history.tsv"); new = not os.path.exists(hp)
        with open(hp, "a", encoding="utf-8") as fh:
            if new: fh.write("date\tcommit\tmust_pass\tmust_total\tgoal_met\tgoal_total\tseconds\tfailed_musts\n")
            fh.write("\t".join(map(str, [today, commit.split()[0] if commit else "", mp, len(must), gp, len(goal), round(secs),
                                         ",".join(r["id"] for r in must if not r["ok"])])) + "\n")
    print(f"must {mp}/{len(must)}   goal {gp}/{len(goal)}   {secs:.0f} s   -> reports/jalasa/STRESS_REPORT.md")
    for r in must:
        if not r["ok"]: print(f"  REGRESSION {r['id']}: {r['why']} -> {r['found']}")
    sys.exit(1 if mp < len(must) else 0)


if __name__ == "__main__":
    main()
