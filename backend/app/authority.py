"""Authority Finder: decide which public authority / portal an RTI belongs to.

Order: keyword rules -> embedding similarity -> chat model choosing among the closest
candidates -> best available guess. It may answer "unknown" and always returns the top
candidates, so the user can pick instead of being forced into a wrong office.
The authority table is demo data; verify against the real directory before launch.
"""
import math
import re
from dataclasses import dataclass

from . import llm, nv

CENTRAL = "Central RTI portal (rtionline.gov.in)"
STATE = "State RTI portal (varies by state)"


@dataclass(frozen=True)
class Authority:
    key: str
    name: str
    level: str  # "central" | "state"
    portal: str
    desc: str
    keywords: tuple[str, ...]


def _a(key, name, level, desc, *kw):
    return Authority(key, name, level, CENTRAL if level == "central" else STATE, desc, kw)


AUTHORITIES = [
    _a("railways", "Ministry of Railways", "central",
       "trains, railway stations, tickets, ticket refunds, IRCTC, railway jobs and parcels",
       "railway", "train", "irctc", "ticket", "refund of ticket", "railway station", "रेल", "ट्रेन", "रेलवे", "tikat"),
    _a("income_tax", "Income Tax Department (CBDT)", "central",
       "income tax returns, tax refunds, TDS, PAN card, assessment, tax notices",
       "income tax", "itr", "tds", "pan card", "tax refund", "assessment year", "आयकर", "इनकम टैक्स"),
    _a("passport", "Passport Seva / Ministry of External Affairs", "central",
       "passport applications, renewal, police verification for passport, visas, passport office",
       "passport", "visa", "पासपोर्ट"),
    _a("epfo", "EPFO / Ministry of Labour", "central",
       "provident fund (PF) accounts, PF withdrawal, EPF claims, employee pension scheme, UAN",
       "epf", "epfo", "pf", "provident fund", "pf withdrawal", "uan", "employee pension", "पीएफ", "भविष्य निधि"),
    _a("uidai", "UIDAI (Aadhaar)", "central",
       "Aadhaar card, Aadhaar enrolment, Aadhaar update or correction, biometric, Aadhaar rejection",
       "aadhaar", "aadhar", "uidai", "आधार"),
    _a("post", "India Post / Department of Posts", "central",
       "post office, speed post, parcels, money orders, postal savings, lost mail",
       "post office", "speed post", "postal", "money order", "parcel", "डाकघर", "डाक"),
    _a("telecom", "BSNL / Department of Telecommunications", "central",
       "BSNL phone and broadband, mobile towers, telecom complaints, landline",
       "bsnl", "telecom", "broadband", "landline", "mobile tower"),
    _a("psu_bank", "Public sector bank (Dept. of Financial Services)", "central",
       "nationalised banks like SBI, PNB, Bank of Baroda: loans, accounts, bank complaints",
       "sbi", "pnb", "bank of baroda", "nationalised bank", "bank loan", "bank account", "बैंक"),
    _a("cbse", "CBSE / UGC / NTA (central education bodies)", "central",
       "CBSE board exams and results, UGC, NTA exams like JEE, NEET, central universities",
       "cbse", "ugc", "nta", "jee", "neet", "central university", "board result"),
    _a("police", "State Police Department", "state",
       "police stations, FIR, complaints to police, investigation, police verification, traffic police",
       "police", "fir", "thana", "thane", "police station", "पुलिस", "एफआईआर", "थाना", "थाने"),
    _a("municipal", "Municipal Corporation / Urban Local Body", "state",
       "city roads, garbage, drains, street lights, property tax, building permission, city services",
       "municipal", "nagar nigam", "nagar palika", "garbage", "drain", "sewer", "road repair", "street light",
       "property tax", "building permission", "pothole", "gaddhe", "sadak", "नगर निगम", "नगर पालिका", "सड़क", "कचरा", "नाली"),
    _a("electricity", "State Electricity Board / DISCOM", "state",
       "electricity supply, power cuts, electricity bills, meters, new connections, DISCOM",
       "electricity", "power cut", "bijli", "meter reading", "electric meter", "discom", "electricity bill",
       "बिजली", "बिजली बिल"),
    _a("water", "Water Supply Department / Jal Board", "state",
       "drinking water supply, pipelines, water bills, sewage, water tankers",
       "water supply", "jal board", "pipeline", "tap water", "water bill", "pani", "jal nigam", "पानी", "जल बोर्ड", "जल निगम"),
    _a("land", "State Revenue / Land Records Department", "state",
       "land records, mutation, khasra, jamabandi, patwari, tehsil, registry, property records",
       "land record", "khasra", "khatauni", "jamabandi", "mutation", "patwari", "tehsil", "registry", "zameen",
       "तहसील", "जमीन", "पटवारी", "खसरा", "जमाबंदी"),
    _a("rto", "State Transport Department / RTO", "state",
       "driving licence, vehicle registration, RTO, challans, number plates, permits",
       "rto", "driving licence", "driving license", "vehicle registration", "challan", "number plate",
       "transport department", "gaadi", "ड्राइविंग लाइसेंस", "आरटीओ", "चालान"),
    _a("health", "State Health Department / Government hospital", "state",
       "government hospitals, doctors, medicines, ambulances, primary health centres, vaccination",
       "hospital", "doctor", "medicine", "ambulance", "health centre", "health center", "phc", "vaccination",
       "dawai", "aspatal", "अस्पताल", "दवाई", "डॉक्टर", "एम्बुलेंस"),
    _a("food", "Food and Civil Supplies Department (ration)", "state",
       "ration cards, ration shops (PDS), fair price shops, wheat and rice distribution",
       "ration card", "ration shop", "ration", "pds", "fair price shop", "rashan", "राशन", "राशन कार्ड"),
    _a("panchayat", "Gram Panchayat / Rural Development Department", "state",
       "village panchayat, MGNREGA job cards and wages, rural housing, sarpanch, village works",
       "panchayat", "mgnrega", "nrega", "job card", "sarpanch", "gram sabha", "village", "gaon", "पंचायत", "मनरेगा", "सरपंच", "गांव", "गाँव"),
    _a("social", "Social Welfare Department (pensions, certificates)", "state",
       "old age pension, widow pension, disability pension and certificates, social welfare schemes",
       "old age pension", "widow pension", "disability pension", "disability certificate", "social welfare",
       "वृद्धावस्था पेंशन", "विधवा पेंशन", "समाज कल्याण"),
    _a("state_school", "State Education Department", "state",
       "government schools, state boards, teacher recruitment, scholarships, mid-day meals",
       "government school", "state board", "teacher recruitment", "scholarship", "mid day meal", "school fees",
       "विद्यालय", "छात्रवृत्ति", "स्कूल"),
    _a("pwd", "Public Works Department (highways, bridges)", "state",
       "state highways, bridges, government building construction, PWD contracts",
       "pwd", "public works", "state highway", "bridge", "flyover", "पीडब्ल्यूडी", "पुल"),
]
BY_KEY = {a.key: a for a in AUTHORITIES}

# Tuned on tests/queries.py. Embedding similarity of the best authority:
# Measured on tests/queries.py HELD_OUT: right answers scored 0.20-0.40 with a gap of >= 0.05
# to the runner-up; vague or off-topic text scored 0.08-0.17.
EMB_ACCEPT = 0.20   # accept without asking the chat model (also needs EMB_MARGIN)
EMB_MARGIN = 0.05
EMB_FLOOR = 0.12    # below this, an authority is not even offered as a candidate

WEAK = {"village", "gaon", "parcel", "bridge", "ticket"}  # common words: count half


def _kw_regex(kw: str) -> re.Pattern:
    if kw.isascii():
        return re.compile(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])")
    return re.compile(re.escape(kw))


_PATTERNS = {a.key: [(k, _kw_regex(k)) for k in a.keywords] for a in AUTHORITIES}


def _rank_rules(text: str) -> list[tuple[float, Authority, list[str]]]:
    t = text.lower()
    out = []
    for a in AUTHORITIES:
        hits = [k for k, p in _PATTERNS[a.key] if p.search(t)]
        score = sum(0.5 if k in WEAK else 2.0 if " " in k else 1.0 for k in hits)
        if score:
            out.append((score, a, hits))
    return sorted(out, key=lambda s: -s[0])


def _result(a: Authority, confidence: float, reason: str, source: str, candidates: list[dict]) -> dict:
    return {"key": a.key, "authority": a.name, "level": a.level, "portal": a.portal,
            "confidence": round(confidence, 2), "reason": reason, "source": source,
            "candidates": candidates}


def _cand(a: Authority, score: float) -> dict:
    return {"key": a.key, "name": a.name, "score": round(score, 2)}


def by_rules(text: str) -> dict | None:
    ranked = _rank_rules(text)
    if not ranked:
        return None
    top, a, hits = ranked[0]
    runner = ranked[1][0] if len(ranked) > 1 else 0
    conf = min(0.9, 0.5 + 0.2 * (top - runner)) if top > runner else 0.4
    return _result(a, conf, f"Matched words: {', '.join(hits)}", "rules",
                   [_cand(x, s) for s, x, _ in ranked[:3]])


# ---- embeddings -----------------------------------------------------------
_vecs: dict[str, list[float]] | None = None


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


async def by_embeddings(text: str) -> list[tuple[float, Authority]] | None:
    global _vecs
    try:
        if _vecs is None:
            docs = [f"{a.name}. {a.desc}. {', '.join(a.keywords)}" for a in AUTHORITIES]
            _vecs = dict(zip((a.key for a in AUTHORITIES), await nv.embed(docs, "passage")))
        q = (await nv.embed([text[:600]], "query"))[0]
    except nv.NvError:
        return None
    return sorted(((_cos(q, _vecs[a.key]), a) for a in AUTHORITIES), key=lambda s: -s[0])


def _emb_conf(sim: float) -> float:
    return max(0.0, min(0.85, 0.5 + (sim - EMB_ACCEPT) * 2.5))


# ---- main entry -----------------------------------------------------------
async def find(text: str) -> dict:
    rule = by_rules(text)
    if rule and rule["confidence"] >= 0.7:
        return rule

    emb = await by_embeddings(text)
    cands = ([_cand(a, s) for s, a in emb[:3] if s >= EMB_FLOOR] if emb else (rule["candidates"] if rule else []))

    if emb and emb[0][0] >= EMB_ACCEPT and emb[0][0] - emb[1][0] >= EMB_MARGIN:
        s, a = emb[0]
        return _result(a, _emb_conf(s), "Closest match to your description", "embeddings", cands)

    # let the chat model choose, but only among plausible candidates, and allow "unknown"
    pool: dict[str, Authority] = {}
    if emb:
        pool.update({a.key: a for s, a in emb[:4] if s >= EMB_FLOOR})
    if rule:
        pool.update({c["key"]: BY_KEY[c["key"]] for c in rule["candidates"]})
    if pool:
        menu = "\n".join(f"- {a.key}: {a.name} ({a.desc})" for a in pool.values())
        out = await llm.chat_json(
            "You route Indian RTI requests to the public authority that holds the records. Choose one key "
            'from the list, or "unknown" if none clearly fits or the request is too vague. Do not guess. '
            'Reply ONLY with JSON: {"key": str, "confidence": number 0-1, "reason": one short sentence}.\n' + menu,
            text[:1500])
        if out and out.get("key") in pool:
            conf = out.get("confidence")
            conf = float(conf) if isinstance(conf, (int, float)) else 0.5
            return _result(pool[out["key"]], min(max(conf, 0.0), 0.9),
                           str(out.get("reason", ""))[:200], "llm", cands)

    if emb and emb[0][0] >= EMB_FLOOR:
        s, a = emb[0]
        return _result(a, min(_emb_conf(s), 0.4), "Possible match; please confirm", "embeddings", cands)
    if rule:
        rule["reason"] += " (not sure; please confirm)"
        return rule
    return {"key": "unknown", "authority": "Could not determine", "level": "unknown", "portal": "",
            "confidence": 0.0, "source": "none", "candidates": cands,
            "reason": "Not enough detail. Mention the department or office and the place."}
