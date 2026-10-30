import re
import unicodedata

from . import config

# Assumption: letters/marks/digits in any script plus common punctuation.
# Replace with the portal's actual allowed set once confirmed.
_ALLOWED_PUNCT = set(" \n\t.,;:()-/'\"?!%&@#+_[]₹")


def is_valid_char(ch: str) -> bool:
    if ch in _ALLOWED_PUNCT:
        return True
    cat = unicodedata.category(ch)
    return cat[0] in ("L", "M", "N")


def validate(text: str) -> dict:
    invalid = sorted({ch for ch in text if not is_valid_char(ch)})
    positions = [i for i, ch in enumerate(text) if not is_valid_char(ch)]
    return {
        "length": len(text),
        "max": config.MAX_DRAFT_CHARS,
        "too_long": len(text) > config.MAX_DRAFT_CHARS,
        "invalid_chars": invalid,
        "invalid_positions": positions[:200],
        "ok": len(text) <= config.MAX_DRAFT_CHARS and not invalid and bool(text.strip()),
    }


def sanitize(text: str) -> str:
    return re.sub(r"[ \t]+\n", "\n", "".join(c for c in text if is_valid_char(c)))
