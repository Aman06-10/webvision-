"""Draft validation against the real RTI Online text box rules.

Source: rtionline.gov.in, "Guidelines for use of RTI Online Portal" (read 2026-10-30):
text is limited to 3000 characters and only A-Z a-z 0-9 and  , . - _ ( ) / @ : & ? \\ %  are allowed.
Longer or non-English text must go in as a PDF in "Supporting document".
Whitespace (space, newline) is assumed allowed; the guidelines do not say.
"""
import re

from . import config

PORTAL_PUNCT = set(" \n\t,.-_()/@:&?\\%")


def is_portal_char(ch: str) -> bool:
    return (ch.isascii() and ch.isalnum()) or ch in PORTAL_PUNCT


# Common characters that have an obvious allowed replacement.
REPLACEMENTS = {"’": "", "‘": "", "'": "", "“": "", "”": "", '"': "", ";": ",", "!": ".", "–": "-", "—": "-",
                "…": "...", "₹": "Rs ", " ": " ", "[": "(", "]": ")", "{": "(", "}": ")", "#": "No ",
                "+": " and ", "*": "", "=": "", "<": "", ">": "", "|": "/"}


def validate(text: str, strict: bool = True) -> dict:
    """strict=True checks the portal's character set (English drafts).
    strict=False (Hindi drafts) skips it and flags that the text must go in as an attachment."""
    bad_idx = [i for i, ch in enumerate(text) if strict and not is_portal_char(ch)]
    over = len(text) > config.MAX_DRAFT_CHARS
    return {
        "length": len(text),
        "max": config.MAX_DRAFT_CHARS,
        "too_long": over,
        "invalid_chars": sorted({text[i] for i in bad_idx}),
        "invalid_positions": bad_idx[:200],
        "needs_attachment": over or (not strict and any(not ch.isascii() for ch in text)),
        "ok": not over and not bad_idx and bool(text.strip()),
    }


def sanitize(text: str) -> str:
    """Replace what we can, then drop anything still not allowed."""
    out = "".join(REPLACEMENTS.get(ch, ch) for ch in text)
    out = "".join(ch for ch in out if is_portal_char(ch))
    return re.sub(r"[ \t]+\n", "\n", re.sub(r" {2,}", " ", out))
