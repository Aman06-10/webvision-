"""Help assistant: retrieve from the RTI knowledge base, then answer from it only.

embed (NVIDIA) -> cosine top-k -> chat model answers using just those passages.
Fallbacks keep it working: keyword overlap if embedding fails, the best passage text if chat fails.
"""
import math
import re

from . import nv
from .kb import PASSAGES

_vectors: list[list[float]] | None = None


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _words(s: str) -> set[str]:
    return set(re.findall(r"\w{3,}", s.lower()))


def _keyword_rank(q: str) -> list[tuple[float, dict]]:
    qw = _words(q)
    scored = [(len(qw & _words(p["title"] + " " + p["text"])) / (len(qw) or 1), p) for p in PASSAGES]
    return sorted(scored, key=lambda s: -s[0])


MIN_SIMILARITY = 0.25  # measured: RTI questions score 0.37-0.60, unrelated ones 0.04-0.14

OFF_TOPIC = {
    "en": "I can only help with questions about filing an RTI request. Try asking about fees, deadlines, appeals or which office to file with.",
    "hi": "मैं केवल आरटीआई आवेदन से जुड़े सवालों में मदद कर सकता हूँ। शुल्क, समय-सीमा, अपील या किस कार्यालय में आवेदन करें, इनके बारे में पूछें।",
}


async def retrieve(question: str, k: int = 3) -> tuple[list[dict], str, bool]:
    """Returns (passages, method, relevant)."""
    global _vectors
    try:
        if _vectors is None:
            _vectors = await nv.embed([f"{p['title']}. {p['text']}" for p in PASSAGES], "passage")
        qv = (await nv.embed([question], "query"))[0]
        ranked = sorted(((_cos(qv, v), p) for v, p in zip(_vectors, PASSAGES)), key=lambda s: -s[0])
        return [p for _, p in ranked[:k]], "embeddings", ranked[0][0] >= MIN_SIMILARITY
    except nv.NvError:
        hits = [p for s, p in _keyword_rank(question)[:k] if s > 0]
        return hits or PASSAGES[:1], "keywords", bool(hits)


async def ask(question: str, lang: str = "en") -> dict:
    passages, method, relevant = await retrieve(question)
    if not relevant:
        return {"answer": OFF_TOPIC.get(lang, OFF_TOPIC["en"]), "sources": [], "retrieval": method,
                "answered_by": "none"}
    context = "\n\n".join(f"[{p['id']}] {p['title']}: {p['text']}" for p in passages)
    language = "Hindi (Devanagari)" if lang == "hi" else "English"
    try:
        answer = await nv.chat(
            "You help Indian citizens use the Right to Information Act. Answer ONLY from the context "
            "passages. If the context does not cover the question, say you are not sure and suggest "
            "asking the Public Information Officer. Do not state any number, duration, amount or rule that "
            "is not written in the context. Be short and plain: at most 5 sentences. "
            "This is general information, not legal advice.",
            f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer in {language}.",
            temperature=0.1, max_tokens=500)
        source = "nvidia-chat"
    except nv.NvError:
        answer = passages[0]["text"]
        source = "passage"
    return {"answer": answer, "sources": [{"id": p["id"], "title": p["title"]} for p in passages],
            "retrieval": method, "answered_by": source}
