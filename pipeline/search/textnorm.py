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


def norm(text):
    return DIAC.sub("", text or "").translate(MAP).lower()


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
