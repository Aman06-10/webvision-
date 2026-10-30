"""Thin JSON/text helpers over nv.chat. Return None on any failure so callers keep a rule-based path."""
import json
import logging

from . import nv

log = logging.getLogger("llm")


def available() -> bool:
    return nv.CHAT.configured


async def chat(system: str, user: str, temperature: float = 0.2) -> str | None:
    try:
        return await nv.chat(system, user, temperature)
    except nv.NvError as e:
        log.warning("chat failed: %s", e)
        return None


async def chat_json(system: str, user: str) -> dict | None:
    text = await chat(system, user, temperature=0)
    if not text:
        return None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
