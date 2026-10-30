"""Authority Finder: decide which public authority / portal an RTI belongs to.

Order: rules -> LLM (only when rules are unsure) -> rules result as fallback.
The authority table is demo data; verify against the real directory before launch.
"""
from dataclasses import dataclass

from . import llm

CENTRAL = "Central RTI portal (rtionline.gov.in)"
STATE = "State RTI portal (varies by state)"


@dataclass(frozen=True)
class Authority:
    key: str
    name: str
    level: str  # "central" | "state"
    portal: str
    keywords: tuple[str, ...]


AUTHORITIES = [
    Authority("railways", "Ministry of Railways", "central", CENTRAL,
              ("railway", "train", "irctc", "ticket", "रेल", "ट्रेन")),
    Authority("income_tax", "Income Tax Department (CBDT)", "central", CENTRAL,
              ("income tax", "itr", "tds", "pan card", "refund", "आयकर")),
    Authority("passport", "Passport Seva / Ministry of External Affairs", "central", CENTRAL,
              ("passport", "visa", "पासपोर्ट")),
    Authority("epfo", "EPFO / Ministry of Labour", "central", CENTRAL,
              ("epf", "pf ", "provident fund", "pension", "भविष्य निधि")),
    Authority("psu_bank", "Public sector bank (Dept. of Financial Services)", "central", CENTRAL,
              ("sbi", "pnb", "bank of baroda", "nationalised bank", "bank loan", "बैंक")),
    Authority("cbse", "CBSE / Ministry of Education", "central", CENTRAL,
              ("cbse", "ugc", "nta", "jee", "neet", "central university")),
    Authority("police", "State Police Department", "state", STATE,
              ("police", "fir", "thana", "पुलिस", "एफआईआर")),
    Authority("municipal", "Municipal Corporation / Urban Local Body", "state", STATE,
              ("municipal", "nagar nigam", "garbage", "drain", "road repair", "property tax",
               "building permission", "नगर निगम")),
    Authority("electricity", "State Electricity Board / DISCOM", "state", STATE,
              ("electricity", "power cut", "bijli", "meter", "discom", "बिजली")),
    Authority("land", "State Revenue / Land Records Department", "state", STATE,
              ("land record", "khasra", "jamabandi", "mutation", "patwari", "तहसील", "जमीन")),
    Authority("state_school", "State Education Department", "state", STATE,
              ("government school", "state board", "teacher recruitment", "scholarship", "विद्यालय")),
]
BY_KEY = {a.key: a for a in AUTHORITIES}


def _score(text: str) -> list[tuple[int, Authority]]:
    t = text.lower()
    scored = [(sum(1 for k in a.keywords if k in t), a) for a in AUTHORITIES]
    return sorted([s for s in scored if s[0] > 0], key=lambda s: -s[0])


def _result(a: Authority, confidence: float, reason: str, source: str) -> dict:
    return {"key": a.key, "authority": a.name, "level": a.level, "portal": a.portal,
            "confidence": round(confidence, 2), "reason": reason, "source": source}


def by_rules(text: str) -> dict | None:
    scored = _score(text)
    if not scored:
        return None
    top, a = scored[0]
    runner = scored[1][0] if len(scored) > 1 else 0
    conf = min(0.9, 0.5 + 0.2 * (top - runner)) if top > runner else 0.4
    hits = [k for k in a.keywords if k in text.lower()]
    return _result(a, conf, f"Matched keywords: {', '.join(hits)}", "rules")


async def find(text: str) -> dict:
    rule = by_rules(text)
    if rule and rule["confidence"] >= 0.7:
        return rule

    menu = "\n".join(f"- {a.key}: {a.name} ({a.level})" for a in AUTHORITIES)
    out = await llm.chat_json(
        "You route Indian RTI requests. Pick exactly one key from the list, or "
        '"unknown". Reply ONLY with JSON: {"key": str, "confidence": 0-1, "reason": str}.\n'
        + menu,
        text[:1500],
    )
    if out and out.get("key") in BY_KEY:
        conf = out.get("confidence")
        conf = float(conf) if isinstance(conf, (int, float)) else 0.6
        return _result(BY_KEY[out["key"]], min(max(conf, 0), 1),
                       str(out.get("reason", ""))[:200], "llm")

    if rule:
        rule["reason"] += " (AI unavailable or unsure; please confirm)"
        return rule
    return {"key": "unknown", "authority": "Could not determine", "level": "unknown",
            "portal": "", "confidence": 0.0,
            "reason": "No match. Choose the authority manually.", "source": "none"}
