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


# ---- request-wording hints ------------------------------------------------
_QUESTION_START = re.compile(r"^\s*(why|whether|how come|what is the reason|kya|kyun|kyon|क्यों|क्या)\b", re.I | re.M)
_OPINION = re.compile(r"\b(opinion|explain|clarify|comment on|justify|suggest|hypothetical|what if|would you)\b", re.I)
_AADHAAR = re.compile(r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)")
_PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_RECORD = re.compile(r"\b(copy|copies|record|records|file|notings?|order|orders|report|reports|document|documents|"
                     r"tender|bill|bills|register|inspection|certified)\b", re.I)


def analyze_request(text: str) -> list[dict]:
    """Hints that make a request less likely to be refused. Advisory only; never blocks."""
    out = []
    t = text or ""
    if not t.strip():
        return out
    if _AADHAAR.search(t) or _PAN.search(t):
        out.append({"code": "id_number", "level": "warning",
                    "message": "This looks like an Aadhaar or PAN number. Remove it: the portal says not to share identity documents, and it makes your request public to more people."})
    if _QUESTION_START.search(t) or _OPINION.search(t):
        out.append({"code": "question_style", "level": "tip",
                    "message": "Questions that ask why or ask for an opinion are often refused, because the Act covers information held in records. Ask for the record instead, for example a copy of the file notings, the order, or the report."})
    if not _RECORD.search(t):
        out.append({"code": "no_record", "level": "tip",
                    "message": "Say which record you want: a copy, file notings, an order, a report, a bill or an inspection of the file."})
    if len(re.findall(r"\?", t)) > 5:
        out.append({"code": "many_questions", "level": "tip",
                    "message": "Many separate questions can slow the reply. Keep one subject per request and number the points."})
    return out
