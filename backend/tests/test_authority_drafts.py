import asyncio

from app import authority, drafts, llm


def run(coro):
    return asyncio.run(coro)


def offline(monkeypatch):
    async def none(text):
        return None
    monkeypatch.setattr(authority, "by_embeddings", none)
    monkeypatch.setattr(llm, "available", lambda: False)


def ranked(*pairs):
    async def f(text):
        rest = [(0.01, a) for a in authority.AUTHORITIES if a.key not in dict(pairs)]
        return sorted([(s, authority.BY_KEY[k]) for k, s in pairs] + rest, key=lambda x: -x[0])
    return f


def test_rules_confident(monkeypatch):
    offline(monkeypatch)
    r = run(authority.find("I want train ticket refund details from railway office, IRCTC"))
    assert r["key"] == "railways" and r["source"] == "rules"


def test_hindi_and_hinglish_keywords(monkeypatch):
    offline(monkeypatch)
    assert run(authority.find("मेरे इलाके की बिजली कटौती"))["key"] == "electricity"
    assert run(authority.find("mera ration card nahi bana"))["key"] == "food"
    assert run(authority.find("pani ki supply roz nahi aati, jal board"))["key"] == "water"


def test_short_keywords_need_word_boundaries(monkeypatch):
    offline(monkeypatch)
    assert authority.by_rules("the spf cream is helpful") is None  # 'pf' inside words must not match


def test_weak_word_alone_is_not_confident(monkeypatch):
    offline(monkeypatch)
    r = run(authority.find("the clinic in our village has no staff"))
    assert r["confidence"] < 0.7


def test_vague_text_is_unknown_with_hint(monkeypatch):
    offline(monkeypatch)
    r = run(authority.find("I need some information"))
    assert r["key"] == "unknown" and "department" in r["reason"]


def test_embeddings_accept_clear_winner(monkeypatch):
    monkeypatch.setattr(authority, "by_embeddings", ranked(("rto", 0.30), ("passport", 0.15)))
    r = run(authority.find("licence to drive a two wheeler never given a test date"))
    assert r["key"] == "rto" and r["source"] == "embeddings"
    assert [c["key"] for c in r["candidates"]] == ["rto", "passport"]  # 0.01-scored filler is dropped


def test_llm_decides_when_embeddings_are_close(monkeypatch):
    monkeypatch.setattr(authority, "by_embeddings", ranked(("electricity", 0.21), ("water", 0.19)))
    async def fake(system, user):
        assert "electricity" in system and "water" in system and "unknown" in system
        return {"key": "electricity", "confidence": 0.8, "reason": "transformer is electrical"}
    monkeypatch.setattr(llm, "chat_json", fake)
    r = run(authority.find("transformer burnt near our house"))
    assert r["key"] == "electricity" and r["source"] == "llm"


def test_llm_can_say_unknown_and_is_not_forced(monkeypatch):
    monkeypatch.setattr(authority, "by_embeddings", ranked(("passport", 0.17), ("railways", 0.17)))
    async def fake(system, user):
        return {"key": "unknown", "confidence": 0.1, "reason": "too vague"}
    monkeypatch.setattr(llm, "chat_json", fake)
    r = run(authority.find("budget of my ministry"))
    assert r["confidence"] <= 0.4 and r["source"] != "llm"


def test_llm_failure_falls_back(monkeypatch):
    monkeypatch.setattr(authority, "by_embeddings", ranked(("police", 0.16)))
    async def fake(system, user):
        return None
    monkeypatch.setattr(llm, "chat_json", fake)
    r = run(authority.find("someone threatened me and nothing was done"))
    assert r["key"] == "police" and r["confidence"] <= 0.4 and "confirm" in r["reason"].lower()


def test_draft_validation():
    assert drafts.validate("नमस्ते, मुझे जानकारी चाहिए।".replace("।", "."))["ok"]
    v = drafts.validate("hello <script> 😀")
    assert not v["ok"] and "<" in v["invalid_chars"]
    assert drafts.validate("a" * 3001)["too_long"]
    assert "<" not in drafts.sanitize("a<b>")
