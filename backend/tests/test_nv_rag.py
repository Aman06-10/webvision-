import asyncio

import pytest

from app import config, nv, rag, voice


def run(c):
    return asyncio.run(c)


def test_limiter_blocks_after_limit(monkeypatch):
    monkeypatch.setattr(config, "KEY_TTS", "k")
    monkeypatch.setattr(config, "RPM_LIMIT", 2)
    svc = nv.Service("tts", "KEY_TTS")
    svc.acquire(); svc.acquire()
    with pytest.raises(nv.RateLimited):
        svc.acquire()
    assert svc.stats()["throttled_locally"] == 1


def test_no_key_raises(monkeypatch):
    monkeypatch.setattr(config, "KEY_STT", "")
    with pytest.raises(nv.NvError):
        nv.Service("stt", "KEY_STT").acquire()


def test_rag_off_topic_makes_no_chat_call(monkeypatch):
    async def fake_embed(texts, input_type):
        return [[1.0, 0.0]] * len(texts) if input_type == "passage" else [[0.0, 1.0]]
    async def boom(*a, **k):
        raise AssertionError("chat must not be called")
    monkeypatch.setattr(rag, "_vectors", None)
    monkeypatch.setattr(nv, "embed", fake_embed)
    monkeypatch.setattr(nv, "chat", boom)
    out = run(rag.ask("capital of France", "en"))
    assert out["answered_by"] == "none" and out["sources"] == []


def test_rag_falls_back_to_keywords_and_passage(monkeypatch):
    async def fail(*a, **k):
        raise nv.NvError("down")
    monkeypatch.setattr(rag, "_vectors", None)
    monkeypatch.setattr(nv, "embed", fail)
    monkeypatch.setattr(nv, "chat", fail)
    out = run(rag.ask("what is the fee for RTI", "en"))
    assert out["retrieval"] == "keywords" and out["answered_by"] == "passage" and "Rs 10" in out["answer"]


def test_beta_languages_flagged(monkeypatch):
    async def fake_chat(system, user, temperature=0.2):
        return "translated"
    monkeypatch.setattr(voice.llm, "chat", fake_chat)
    out = run(voice.translate_text("x", "ta", "en"))
    assert out["quality"] == "beta"


def test_verified_pair_uses_riva(monkeypatch):
    async def fake(text, src, tgt):
        assert (src, tgt) == ("hi", "en")
        return "ok"
    monkeypatch.setattr(nv, "translate", fake)
    out = run(voice.translate_text("x", "hi", "en"))
    assert out["quality"] == "verified" and out["engine"] == "nvidia-riva-translate"
