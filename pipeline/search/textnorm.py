"""Shared normalisation for the search layer (index and queries must use the same rules).

Surface form ("norm"): harakat, Quranic marks, tatweel and PUA removed; alif variants -> ا;
ى/ی/ي -> ي; ک/ك -> ك; ة -> ه; ؤ -> و; ئ -> ي; Persian half-space (ZWNJ) joined;
Arabic-Indic digits -> ASCII. Case of Latin text folded.
Roots come from CAMeL Tools (morphology-db-msa-r13), stored per word type; '#' in a CAMeL
root (weak radical) is written 'ـ' so it survives the FTS tokenizer.
"""
import re

DIAC = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ-]")
MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ٲ": "ا", "ٳ": "ا",
    "ى": "ي", "ی": "ي", "ې": "ي", "ۍ": "ي",
    "ک": "ك", "ڪ": "ك",
    "ة": "ه", "ۀ": "ه", "ە": "ه", "ھ": "ه", "ۃ": "ه",
    "ؤ": "و", "ئ": "ي",
    "‌": "", "‍": "", "‎": "", "‏": "", "﻿": "",
    **{chr(0x0660 + i): str(i) for i in range(10)},
    **{chr(0x06F0 + i): str(i) for i in range(10)},
})
WORD = re.compile(r"[ء-غف-يٱ-ۓپچژگکی]+")


_PAIRS = [(chr(k), v) for k, v in MAP.items()]     # no replacement is itself a key, so one pass per character is exact


def norm(text):
    """v49: the same result as DIAC.sub("", text).translate(MAP).lower(), about five times faster: str.translate with a
    dict looks every character up in Python; a replace per mapped character runs in C and skips characters absent."""
    s = DIAC.sub("", text or "")
    for k, v in _PAIRS:
        if k in s: s = s.replace(k, v)
    return s.lower()


def words(text):
    """Arabic-script word tokens of the diacritic-stripped (not yet normalised) text."""
    return WORD.findall(DIAC.sub("", text or ""))


def root_token(camel_root):
    return camel_root.replace(".", "").replace("#", "ـ")


def root_query_variants(root):
    """'وكل' -> ['وكل', 'ـكل'] : also match CAMeL's weak-radical notation."""
    r = norm(root).replace(".", "").replace(" ", "")
    out = {r}
    for i, ch in enumerate(r):
        if ch in "اوي":
            out.add(r[:i] + "ـ" + r[i + 1:])
    return sorted(out)
