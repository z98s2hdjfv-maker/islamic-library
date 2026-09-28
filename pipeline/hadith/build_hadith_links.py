#!/usr/bin/env python3
"""
build_hadith_links.py - v17: links over the v16 hadith layer (apparatus/hadith/).

1. Parallels. Versions of the same hadith across (and within) collections are grouped by the
   wording of the matn: MinHash over 3-word shingles of the normalised matn, LSH candidates,
   kept when shingle overlap (Jaccard) >= 0.3, then grouped transitively. Matns under 6 words
   are not grouped (too generic). A group holding both al-Bukhari and Muslim is flagged
   agreed_upon (muttafaq 'alayh) - by wording only, unverified.
   -> apparatus/hadith_links/parallels.tsv.gz   group, hadith_id, collection, number

2. Narrators. Ibn Hajar's Taqrib al-Tahdhib (corpus/rijal/) is parsed into one row per entry with
   his grade and its rank on his own 12-step scale (1 Companion ... 12 liar/fabricator).
   -> apparatus/rijal/taqrib_index.tsv.gz
   Each isnad (last chain after any tahwil "ح") is split into narrator names; a name is linked
   to a Taqrib entry only when exactly one entry fits, tried in this order: the conventional
   identifications in catalogs/narrator_aliases.tsv (e.g. al-A'mash = Sulayman b. Mihran; reviewed
   list, ambiguous names like a bare "Sufyan" are never linked); the start of an entry's name; any
   contiguous part of an entry's name; each of these narrowed by Ibn Hajar's six-book sigla (kh, m,
   d, t, s, q) when the hadith is in one of the Six Books. Every link records how it was made.
   -> apparatus/hadith_links/chains.jsonl.gz    per hadith: narrators with Taqrib no., grade, rank;
                                                 weakest_rank among linked narrators; share linked
   weakest_rank describes the linked narrators only. It is NOT a grade of the hadith: it ignores
   unlinked narrators, breaks in the chain, hidden defects ('ilal) and corroboration.

Summary: catalogs/hadith_links_summary.json. Everything derived automatically; status unverified.
Usage: build_hadith_links.py [--repo .]
"""
import argparse, collections, csv, glob, gzip, io, json, os, re, sys, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "search"))
from textnorm import norm

WORD = re.compile(r"[ء-ي]+")
RANKS = [(1, r"(?:ال)?صحابي(?:ة)?\b|له صحبة|له رؤية|أم المؤمنين|أحد العبادلة|أحد العشرة|أمير المؤمنين(?! في الحديث)|شهد بدرا|الخليفة"),
         (2, r"\bثقة (?:ثبت|حافظ|حجة|متقن|ثقة|فقيه|عابد|إمام)|\bإمام\b|\bأمير المؤمنين في الحديث|متفق على جلالته"),
         (3, r"\bثقة\b"),
         (5, r"\bصدوق (?:يخطىء|يخطئ|يهم|له أوهام|سيء الحفظ|تغير|اختلط|خلط|ربما|يدلس|كثير)"),
         (4, r"\bصدوق\b"), (6, r"\bمقبول\b|\bلين الحديث|\bفيه لين"), (7, r"\bمستور\b|\bمجهول الحال"),
         (8, r"\bضعيف\b|\bضعف\b"), (9, r"\bمجهول\b|\bلا يعرف"), (10, r"\bمتروك\b|\bواه\b"),
         (11, r"\bمتهم\b"), (12, r"\bكذاب\b|\bوضاع\b|\bكذبوه")]
RANK_NAME = {1: "Companion", 2: "thiqa+ (highest)", 3: "thiqa", 4: "saduq", 5: "saduq with errors", 6: "maqbul",
             7: "mastur", 8: "da'if", 9: "majhul", 10: "matruk", 11: "muttaham", 12: "kadhdhab"}
SEPW = {"عن", "سمعت", "سمع", "أن", "أنه", "أنها", "حدثني", "حدثنا", "وحدثنا", "وحدثني", "أخبرني", "أخبرنا",
        "وأخبرنا", "حدثه", "أخبره", "ثنا", "نا", "أنا", "أنبأنا", "أنبأ", "قال", "قالا", "قالوا", "قالت", "يقول", "ح"}
DROP = {"أبيه", "أبي", "جده", "أمه", "عمه", "رجل", "رجلا", "غيره", "أصحابه", "فلان", "شيخ", "أشياخه", "مثله", "نحوه"}


def J(path):
    return (json.loads(l) for l in gzip.open(path, "rt", encoding="utf-8"))


def gzw(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fz = open(path, "wb"); gz = gzip.GzipFile(fileobj=fz, mode="wb", mtime=0, filename="")
    fo = io.TextIOWrapper(gz, encoding="utf-8", newline="\n"); fo._fz = fz; return fo


def gzclose(fo):
    fo.close(); fo._fz.close()


# ---------- 1. parallels ----------
JACCARD = float(os.environ.get("PARALLEL_JACCARD", "0.3"))
def parallels(repo, H):
    K, BANDS = 32, 16; ROWS = K // BANDS; P = (1 << 61) - 1
    rng = np.random.default_rng(20260928)
    A = rng.integers(1, P - 1, K, dtype=np.uint64); B = rng.integers(0, P - 1, K, dtype=np.uint64)
    sh = []; sig = np.full((len(H), K), np.iinfo(np.uint64).max, dtype=np.uint64)
    for i, h in enumerate(H):
        w = WORD.findall(norm(h["matn"]))
        s = {zlib.crc32(" ".join(w[j:j + 3]).encode()) for j in range(len(w) - 2)} if len(w) >= 6 else set()
        sh.append(s)
        if s:
            x = np.fromiter(s, dtype=np.uint64)
            sig[i] = ((np.outer(x, A) + B) % np.uint64(P)).min(axis=0) if len(x) < 4000 else sig[i]
    parent = list(range(len(H)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    pairs = 0
    for b in range(BANDS):
        buckets = collections.defaultdict(list)
        for i in range(len(H)):
            if sh[i]: buckets[sig[i, b * ROWS:(b + 1) * ROWS].tobytes()].append(i)
        for ids in buckets.values():
            if len(ids) < 2 or len(ids) > 400: continue      # huge buckets = boilerplate
            base = ids[0]
            for j in ids[1:]:
                ra, rb = find(base), find(j)
                if ra == rb: continue
                s1, s2 = sh[base], sh[j]
                if len(s1 & s2) / len(s1 | s2) >= JACCARD: parent[ra] = rb; pairs += 1
    groups = collections.defaultdict(list)
    for i in range(len(H)):
        if sh[i]: groups[find(i)].append(i)
    groups = [g for g in groups.values() if len(g) > 1]
    groups.sort(key=lambda g: min(H[i]["id"] for i in g))
    out = gzw(os.path.join(repo, "apparatus/hadith_links/parallels.tsv.gz"))
    out.write("group\thadith_id\tcollection\tnumber\n")
    gid_of = {}; agreed = 0; cross = 0
    for k, g in enumerate(groups, 1):
        gid = f"P{k:06d}"; cols = {H[i]["collection"] for i in g}
        if {"0256Bukhari.Sahih", "0261Muslim.Sahih"} <= cols: agreed += 1
        if len(cols) > 1: cross += 1
        for i in sorted(g, key=lambda i: H[i]["id"]):
            gid_of[H[i]["id"]] = (gid, len(cols), "0256Bukhari.Sahih" in cols and "0261Muslim.Sahih" in cols)
            out.write(f"{gid}\t{H[i]['id']}\t{H[i]['collection']}\t{H[i]['number']}\n")
    gzclose(out)
    return gid_of, {"groups": len(groups), "groups_across_collections": cross, "agreed_upon_groups": agreed,
                    "hadith_in_groups": sum(len(g) for g in groups)}


# ---------- 2. narrators ----------
GLOSS = re.compile(r"^و?(?:ب|ال)?(?:فتح|كسر|ضم|سكون|تصغير|التصغير|مهملة|معجمة|موحدة|مثناة|مثلثة|نون|تحتانية|فوقانية|"
                   r"المهملة|المعجمة|الموحدة|المثناة|المثلثة|النون|زاي|الزاي|راء|الراء|قاف|القاف|فاء|الفاء|تشديد|"
                   r"التشديد|تخفيف|التخفيف|همزة|الهمزة|ياء|الياء|واو|الواو|لام|اللام|ميم|الميم|دال|الدال|عين|العين)$")
STOP = {"بن", "ابن", "بنت", "أبو", "ابو", "أبي", "أم", "مولى", "مولاهم", "نزيل"}


def strip_gloss(name):
    """Taqrib names carry spelling notes (bi-fath awwalihi ...); drop them up to the next name part."""
    out, skipping = [], False
    for w in name.split():
        if GLOSS.match(w) or (w.startswith(("بفتح", "بكسر", "بضم", "بسكون", "بالتصغير", "بمهملة", "بمعجمة", "بموحدة",
                                             "بمثناة", "بمثلثة", "بنون", "بتحتانية", "بفوقانية", "بزاي", "براء", "بقاف"))):
            skipping = True; continue
        if skipping and w not in STOP: continue
        skipping = False; out.append(w)
    return " ".join(out)


def name_norm(s):
    s = norm(s); s = re.sub(r"[^ء-ي ]", " ", s)
    s = re.sub(r"\bابي\b", "ابو", s); s = re.sub(r"\bابا\b", "ابو", s); s = re.sub(r"\bابن\b", "بن", s)
    return " ".join(s.split())


DROPN = None


def taqrib(repo):
    path = os.path.join(repo, "corpus/rijal/0852IbnHajarCasqalani.TaqribTahdhib.jsonl.gz")
    rows = []
    for r in J(path):
        if r["kind"] != "para": continue
        m = re.match(r"^\s*#+\s*\${1,2}\s+(\d{1,5})\s+(.*)$", r.get("text") or "")   # $$ = women
        if not m: continue
        t = m.group(2); best = None
        for rk, p in RANKS:
            g = re.search(p, t)
            if g and (best is None or g.start() < best[1]): best = (rk, g.start(), g.group(0))
        cut = min([x for x in (best[1] if best else None, t.find(" من ال")) if x is not None and x > 0] or [len(t)])
        tail = t.split()[-4:]; codes = set()
        for w in tail:
            if re.fullmatch(r"[خمدتسقع4]{1,3}", w): codes |= set(w)
        if "ع" in codes: codes |= set("خمدتسق")
        if "4" in codes: codes |= set("دتسق")
        rows.append({"no": int(m.group(1)), "name": t[:cut].strip(), "grade": best[2] if best else "",
                     "rank": best[0] if best else None, "text": t, "uid": r["id"], "codes": "".join(sorted(codes))})
    out = gzw(os.path.join(repo, "apparatus/rijal/taqrib_index.tsv.gz"))
    out.write("taqrib_no\tname\tgrade\trank\trank_name\tsix_book_codes\tentry_text\tcorpus_uid\n")
    for x in rows:
        out.write(f"{x['no']}\t{x['name']}\t{x['grade']}\t{x['rank'] or ''}\t{RANK_NAME.get(x['rank'], '')}\t{x['codes']}\t{x['text']}\t{x['uid']}\n")
    gzclose(out)
    pre, inside = collections.defaultdict(set), collections.defaultdict(set)
    for k, x in enumerate(rows):
        w = name_norm(strip_gloss(x["name"])).split()
        for n in range(1, 9): pre[" ".join(w[:n])].add(k)
        for j, t in enumerate(w):   # kunya (not "son of Abu X"), nisba/laqab, and "bin X" lineage grams
            if t in ("ابو", "ام") and (j == 0 or w[j - 1] not in ("بن", "بنت")):
                for n in range(2, 5): inside[" ".join(w[j:j + n])].add(k)
            elif t.startswith("ال") and j > 0:
                inside[t].add(k)
            elif t == "بن" and j > 0:
                for n in range(2, 5): inside[" ".join(w[j:j + n])].add(k)
    alias = {}
    for a in csv.DictReader(open(os.path.join(repo, "catalogs/narrator_aliases.tsv"), encoding="utf-8"), delimiter="\t"):
        if not a["taqrib_key"]: continue
        key = name_norm(a["taqrib_key"]); hit = [k for k, x in enumerate(rows) if name_norm(x["text"]).startswith(key)
                                                 or name_norm(strip_gloss(x["text"])).startswith(name_norm(strip_gloss(a["taqrib_key"])))]
        if len(hit) == 1: alias[name_norm(a["alias"])] = hit[0]
        else: print("alias not unique, skipped:", a["alias"], len(hit))
    return rows, (pre, inside, alias)


COLL_CODE = {"0256Bukhari.Sahih": "خ", "0261Muslim.Sahih": "م", "0275AbuDawudSijistani.Sunan": "د",
             "0279Tirmidhi.Sunan": "ت", "0303Nasai.SunanSughra": "س", "0303Nasai.SunanKubra": "س", "0273IbnMaja.Sunan": "ق"}


def resolve(nn, idx, rows, coll):
    pre, inside, alias = idx
    if nn in alias: return alias[nn], "alias"
    kunya_or_nisba = nn.startswith(("ابو ", "ام ", "ال")) or " " not in nn and nn.startswith("ال")
    for how, cand in (("prefix", pre.get(nn, set())), ("contains", inside.get(nn, set()))):
        if how == "contains" and not kunya_or_nisba:            # a plain name inside someone's lineage is not him
            code = COLL_CODE.get(coll)
            c2 = [k for k in cand if code and code in rows[k]["codes"]]
            return (c2[0], "contains+book_code") if len(c2) == 1 and nn.startswith("بن ") else (None, len(cand) or 0)
        if len(cand) == 1: return next(iter(cand)), how
        code = COLL_CODE.get(coll)
        bare_kunya = len(nn.split()) == 2 and nn.split()[0] in ("ابو", "ام")   # e.g. "Abu Hazim": too many share it
        if len(cand) > 1 and code and not bare_kunya:
            c2 = [k for k in cand if code in rows[k]["codes"]]
            if len(c2) == 1: return c2[0], how + "+book_code"
        if cand: return None, len(cand)
    return None, 0


def chain_names(isnad):
    t = re.sub(r"\(\d+\)", " ", isnad)
    t = re.split(r"\sح\s", " " + t + " ")[-1]                        # last chain after tahwil
    t = re.sub(r"(?:صلى الله عليه (?:وآله )?وسلم|رضي الله (?:عنهما|عنهم|عنها|عنه))", " ", t)
    t = re.sub(r"\bيعني\s+(?:ابن|بن)\b", "بن", t); t = re.sub(r"\b(?:يعني|وهو|هو)\b[^،,]*", " ", t)
    names, cur = [], []
    for w in re.split(r"[\s،,:.]+", t):
        if not w: continue
        if w in SEPW or w.startswith("و") and w[1:] in SEPW:
            if cur: names.append(" ".join(cur)); cur = []
        else: cur.append(w)
    if cur: names.append(" ".join(cur))
    out = []
    for n in names:
        n = re.sub(r"^(?:و)", "", n) if n.startswith("وابن") else n
        nn = name_norm(n)
        if not nn or nn in DROPN or "رسول الله" in nn or "النبي" in nn or len(nn) < 3 or len(nn.split()) > 9: continue
        out.append((n, nn))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default="."); repo = ap.parse_args().repo
    H = []
    for p in sorted(glob.glob(os.path.join(repo, "apparatus/hadith/*.jsonl.gz"))):
        for r in J(p): H.append({k: r[k] for k in ("id", "collection", "number", "isnad", "matn", "narrator")})
    print(len(H), "hadith", flush=True)
    gid_of, psum = parallels(repo, H); print("parallels", psum, flush=True)
    global DROPN; DROPN = {name_norm(x) for x in DROP}
    rows, idx = taqrib(repo); print(len(rows), "Taqrib entries", flush=True)
    out = gzw(os.path.join(repo, "apparatus/hadith_links/chains.jsonl.gz"))
    st = collections.Counter(); weakest = collections.Counter()
    for h in H:
        nar = []
        for raw, nn in chain_names(h["isnad"]):
            k, how = resolve(nn, idx, rows, h["collection"])
            if k is not None:
                x = rows[k]; st["by_" + how] += 1
                nar.append({"name": raw, "taqrib_no": x["no"], "taqrib_name": x["name"], "grade": x["grade"],
                            "rank": x["rank"], "match": how})
            else:
                nar.append({"name": raw, "candidates": how})
        linked = [n for n in nar if "taqrib_no" in n and n["rank"]]
        wr = max((n["rank"] for n in linked), default=None)
        g = gid_of.get(h["id"])
        rec = {"hadith_id": h["id"], "parallel_group": g[0] if g else None,
               "parallel_collections": g[1] if g else 1, "agreed_upon": bool(g and g[2]),
               "narrators": nar, "linked": len(linked), "names": len(nar),
               "weakest_rank": wr, "weakest_rank_name": RANK_NAME.get(wr), "status": "unverified"}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        st["names"] += len(nar); st["linked"] += len(linked); st["hadith"] += 1
        st["fully_linked"] += bool(nar) and len(linked) == len(nar)
        if wr: weakest[RANK_NAME[wr]] += 1
    gzclose(out)
    summary = {"note": "derived automatically; unverified. weakest_rank is not a grade of the hadith.",
               "parallels": psum, "taqrib_entries": len(rows),
               "narrator_names": st["names"], "narrator_names_linked": st["linked"],
               "share_linked": round(st["linked"] / max(st["names"], 1), 3),
               "hadith_fully_linked": st["fully_linked"], "weakest_rank_of_linked": dict(weakest.most_common()),
               "link_methods": {k[3:]: v for k, v in st.items() if k.startswith("by_")}}
    json.dump(summary, open(os.path.join(repo, "catalogs/hadith_links_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
