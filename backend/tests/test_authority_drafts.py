import asyncio

from app import authority, drafts, llm


def run(coro):
    return asyncio.run(coro)


def test_rules_confident(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)
    r = run(authority.find("I want train ticket refund details from railway office, IRCTC"))
    assert r["key"] == "railways" and r["source"] == "rules"


def test_hindi_keywords(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)
    assert run(authority.find("मेरे इलाके की बिजली कटौती"))["key"] == "electricity"


def test_no_match_without_llm(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)
    assert run(authority.find("something unrelated"))["key"] == "unknown"


def test_llm_used_when_rules_unsure(monkeypatch):
    async def fake(system, user):
        return {"key": "police", "confidence": 0.8, "reason": "mentions a complaint"}
    monkeypatch.setattr(llm, "chat_json", fake)
    r = run(authority.find("my complaint was ignored"))
    assert r["key"] == "police" and r["source"] == "llm"


def test_llm_failure_falls_back_to_rules(monkeypatch):
    async def fake(system, user):
        return None
    monkeypatch.setattr(llm, "chat_json", fake)
    r = run(authority.find("tax refund and a train"))
    assert r["source"] == "rules" and "confirm" in r["reason"]


def test_draft_validation():
    assert drafts.validate("नमस्ते, मुझे जानकारी चाहिए।".replace("।", "."))["ok"]
    v = drafts.validate("hello <script> 😀")
    assert not v["ok"] and "<" in v["invalid_chars"]
    assert drafts.validate("a" * 3001)["too_long"]
    assert "<" not in drafts.sanitize("a<b>")
