#!/usr/bin/env python3
"""
clean_fusus_textlayer.py - rebuild a clean Arabic text of Fusus al-hikam, ed. Sayyid Nizam al-Din
Ahmad (Cairo 2015), from the publisher PDF's own text layer. Deterministic; nothing retyped.

Why: the PDF text layer (and sources/fusus/..._text_dump.txt) is damaged in three ways:
  1. doubled glyphs - each presentation-form glyph is followed by its base letter (ﺍا = alif twice);
  2. 71 private-use (PUA) codes - the XWZar font's positioned harakat, lam/alif variants
     (lam-alif is drawn as two PUA glyphs, so "la" vanished from naive extraction), kashida;
  3. bidi control marks, and presentation forms instead of base letters.
Fix: map each PUA code to Unicode from the embedded fonts' own glyph names (afii57454_alt4 ->
U+064E, uniFEDF_alt -> lam, kashidaautoarabic -> dropped), drop the duplicate base after each
presentation form, fold presentation forms (NFKC), drop duplicate extended digits (١۱ -> ١),
remove bidi marks, NFC, move a word-final haraka that extraction pushed onto the next word
back to its word ("العِلْم ُكَانَ" -> "العِلْمُ كَانَ"), rejoin the split article ("ا لعلم" -> "العلم").
Known residue (not fixable from the text layer): harakat sometimes precede their letter,
occasional word splits ("ح يث"), footnote/line order follows pdftotext. Search layer strips harakat.

Output: one JSONL row per PDF page: {id, work, leaf, text_raw (pdftotext), text (clean), provenance}
Usage: clean_fusus_textlayer.py --pdf Fusus...pdf --out fusus.nizamaldin_textlayer.jsonl --report r.json
Needs: poppler pdftotext, pip pymupdf fonttools.
"""
import argparse, hashlib, io, json, re, subprocess, unicodedata, collections
PDF_SHA = "0fdd3fdc11398b11dcff719852ae000f8eb747e857262a2bf40479301c8aaeb7"
AFII = {51: "ً", 52: "ٌ", 53: "ٍ", 54: "َ", 55: "ُ", 56: "ِ", 57: "ّ", 58: "ْ"}
BIDI = dict.fromkeys(map(ord, "‪‫‬‭‮‎‏﻿"), None)

def glyphname_to_text(g):
    if g == "kashidaautoarabic": return ""
    g = re.sub(r"(_alt\d*|alt\d*|\.fin|\.init|\.medi)+$", "", g)
    out = ""
    for part in g.split("_"):
        m = re.fullmatch(r"afii574(\d\d)", part)
        if m: out += AFII[int(m.group(1))]; continue
        m = re.fullmatch(r"uni((?:[0-9A-F]{4})+)", part)
        if m:
            for k in range(0, len(m.group(1)), 4):
                out += unicodedata.normalize("NFKC", chr(int(m.group(1)[k:k+4], 16))).replace(" ", "")
            continue
        raise ValueError("unmapped glyph name " + g)
    return out

def pua_table(pdf):
    import pymupdf
    from fontTools.ttLib import TTFont
    doc = pymupdf.open(pdf); table = {}; done = set()
    for pno in range(len(doc)):
        for f in doc[pno].get_fonts():
            x = f[0]
            if x in done: continue
            done.add(x); fd = doc.xref_object(x)
            m = re.search(r"/ToUnicode (\d+) 0 R", fd)
            if not m: continue
            s = doc.xref_stream(int(m.group(1))).decode("latin1")
            maps = re.findall(r"<([0-9a-fA-F]{2,4})><([0-9a-fA-F]{2,4})><([0-9a-fA-F]{4})>", s)
            maps += [(a, a, b) for a, b in re.findall(r"<([0-9a-fA-F]{2,4})>\s*<([0-9a-fA-F]{4})>", s)]
            pua = [(int(a, 16), int(u, 16)) for a, b, u in maps if 0xE000 <= int(u, 16) <= 0xF8FF]
            if not pua: continue
            tt = TTFont(io.BytesIO(doc.extract_font(x)[3]))
            for code, U in pua:
                for t in tt["cmap"].tables:
                    g = t.cmap.get(code) or t.cmap.get(0xF000 + code)
                    if g:
                        table.setdefault(chr(U), (g, glyphname_to_text(g))); break
    return table

EXT = {0x06F0 + i: 0x0660 + i for i in range(10)}
def clean(raw, pua, stats):
    t = raw.translate(BIDI); out = []; i = 0
    while i < len(t):
        c = t[i]; o = ord(c)
        if 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF:
            b = unicodedata.normalize("NFKC", c).replace(" ", "")
            out.append(b); j = i + 1
            if b and t[j:j+len(b)] == b: j += len(b); stats["dup_removed"] += 1
            i = j; continue
        if 0x0660 <= o <= 0x0669 and i + 1 < len(t) and EXT.get(ord(t[i+1])) == o:
            out.append(c); i += 2; stats["dup_digit"] += 1; continue
        if 0xE000 <= o <= 0xF8FF:
            if c in pua: out.append(pua[c][1]); stats["pua_mapped"] += 1
            else: stats["pua_unmapped"] += 1
            i += 1; continue
        out.append(c); i += 1
    s = unicodedata.normalize("NFC", "".join(out))
    s = re.sub(r"(?<=\S) ([\u064B-\u0652\u0670]+)(?=\S)", r"\1 ", s)   # final haraka pushed onto next word
    s = re.sub(r"(?<!\S)ا ?([\u064B-\u0652]*) (ل)", r"ا\1\2", s)       # article split by bidi marks
    s = re.sub(r"[ \t]+", " ", s)
    s = "\n".join(l.strip() for l in s.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", s).strip()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pdf", required=True); ap.add_argument("--out", required=True); ap.add_argument("--report", required=True)
    a = ap.parse_args()
    h = hashlib.sha256(open(a.pdf, "rb").read()).hexdigest()
    if h != PDF_SHA: raise SystemExit("PDF sha256 mismatch: " + h)
    pua = pua_table(a.pdf)
    npages = int(re.search(r"Pages:\s+(\d+)", subprocess.check_output(["pdfinfo", a.pdf], text=True)).group(1))
    ver = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.splitlines()[0]
    stats = collections.Counter()
    with open(a.out, "w", encoding="utf-8") as fo:
        for p in range(1, npages + 1):
            raw = subprocess.check_output(["pdftotext", "-f", str(p), "-l", str(p), a.pdf, "-"]).decode("utf-8")
            fo.write(json.dumps({"id": f"urn:lib:ibnarabi.fusus.nizamaldin_textlayer:{p:05d}",
                "work": "Fusus al-hikam, ed. Sayyid Nizam al-Din Ahmad (Cairo 2015, critical)", "leaf": p,
                "text_raw": raw, "text": clean(raw, pua, stats),
                "provenance": {"source": "release v1-assets PDF", "pdf_sha256": h, "extractor": ver,
                               "method": "pdf_textlayer_cleaned", "source_type": "pdf_textlayer_cleaned", "status": "unverified"}},
                ensure_ascii=False) + "\n")
    rep = {"pages": npages, "pdf_sha256": h, "extractor": ver, "stats": dict(stats),
           "pua_map": {f"{ord(k):04X}": {"glyph": v[0], "text": v[1]} for k, v in sorted(pua.items())}}
    json.dump(rep, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep["stats"]), "pua codes", len(pua))

if __name__ == "__main__":
    main()
