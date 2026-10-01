"""
pages.py - v42: exact printed pages inside OpenITI records.

OpenITI marks page boundaries with PageV18P056 (and, in some Shamela-derived versions, PageEndV18P494). Both mark the
END of that page: text after the marker is on the next page. Tested 2026-10-01 against the Shamela Futuhat, which
carries true printed pages: in 116 of 119 passages the printed page was the marker's page + 1 (3 were equal).
So a record's `page_before` is the page that ended before it; the record STARTS on page_before + 1, and a passage
inside a long record (al-Tamhid's fitra chapter is one record) is on 1 + the last marker before it.
"""
import re

MARK = re.compile(r"Page(?:End)?V(\d+)P(\d+)")


def segments(rec):
    """-> [(vol, page, raw_text)] : the record's text cut at its page markers, each piece with its true page."""
    raw = rec.get("text_raw") if isinstance(rec.get("text_raw"), str) else rec.get("text") or ""
    vol, pb = rec.get("vol"), rec.get("page_before")
    page = pb + 1 if isinstance(pb, int) else rec.get("page") if isinstance(rec.get("page"), int) else None
    out, pos = [], 0
    for m in MARK.finditer(raw):
        out.append((vol, page, raw[pos:m.start()]))
        vol, page, pos = int(m.group(1)), int(m.group(2)) + 1, m.end()
    out.append((vol, page, raw[pos:]))
    return [s for s in out if s[2].strip()]


def start_page(rec):
    pb = rec.get("page_before")
    return pb + 1 if isinstance(pb, int) else rec.get("page")


def fmt(vol, page):
    if page is None: return ""
    return f"{vol}:{page}" if vol is not None else f"p. {page}"
