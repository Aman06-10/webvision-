"""All NVIDIA calls in one place, with a per-service rate limiter and usage counters.

Every function raises NvError (or RateLimited) on failure; callers decide the fallback.
"""
import asyncio
import io
import time
import wave
from collections import deque

import httpx

from . import config


class NvError(Exception):
    pass


class RateLimited(NvError):
    pass


class Service:
    def __init__(self, name: str, key_attr: str):
        self.name, self.key_attr = name, key_attr
        self.window: deque[float] = deque()
        self.total = self.errors = self.limited = 0
        self.last_error = ""

    @property
    def key(self) -> str:
        return getattr(config, self.key_attr)

    @property
    def configured(self) -> bool:
        return bool(self.key)

    def acquire(self) -> None:
        if not self.configured:
            raise NvError(f"{self.name}: no API key")
        now = time.monotonic()
        while self.window and now - self.window[0] > 60:
            self.window.popleft()
        if len(self.window) >= config.RPM_LIMIT:
            self.limited += 1
            raise RateLimited(f"{self.name}: local limit of {config.RPM_LIMIT}/min reached")
        self.window.append(now)
        self.total += 1

    def fail(self, msg: str) -> NvError:
        self.errors += 1
        self.last_error = msg[:160]
        return RateLimited(msg) if "429" in msg else NvError(msg)

    def stats(self) -> dict:
        now = time.monotonic()
        recent = sum(1 for t in self.window if now - t <= 60)
        return {"configured": self.configured, "calls_total": self.total, "calls_last_minute": recent,
                "limit_per_minute": config.RPM_LIMIT, "errors": self.errors,
                "throttled_locally": self.limited, "last_error": self.last_error}


CHAT = Service("chat", "KEY_CHAT")
EMBED = Service("embed", "KEY_EMBED")
TRANSLATE = Service("translate", "KEY_TRANSLATE")
TTS = Service("tts", "KEY_TTS")
STT = Service("stt", "KEY_STT")
ALL = [CHAT, EMBED, TRANSLATE, TTS, STT]


async def _post_json(svc: Service, path: str, body: dict) -> dict:
    svc.acquire()
    try:
        async with httpx.AsyncClient(timeout=config.HTTP_TIMEOUT_S) as http:
            r = await http.post(config.NVIDIA_BASE_URL + path, json=body,
                                headers={"Authorization": f"Bearer {svc.key}"})
    except httpx.HTTPError as e:
        raise svc.fail(f"{svc.name}: {type(e).__name__}")
    if r.status_code != 200:
        raise svc.fail(f"{svc.name}: HTTP {r.status_code} {r.text[:100]}")
    return r.json()


async def chat(system: str, user: str, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    out = await _post_json(CHAT, "/chat/completions", {
        "model": config.CHAT_MODEL, "messages": msgs, "temperature": temperature,
        "max_tokens": max_tokens, "chat_template_kwargs": {"enable_thinking": False}})
    text = (out["choices"][0]["message"].get("content") or "").strip()
    if not text:
        raise CHAT.fail("chat: empty reply")
    return text


async def translate(text: str, src: str, tgt: str) -> str:
    """Riva translate. Only hi<->en has been verified; the prompt must be the bare 'xx-yy' pair."""
    out = await _post_json(TRANSLATE, "/chat/completions", {
        "model": config.TRANSLATE_MODEL, "temperature": 0, "max_tokens": 2048,
        "messages": [{"role": "system", "content": f"{src}-{tgt}"}, {"role": "user", "content": text}]})
    res = (out["choices"][0]["message"].get("content") or "").strip()
    if not res:
        raise TRANSLATE.fail("translate: empty reply")
    return res


async def embed(texts: list[str], input_type: str) -> list[list[float]]:
    out = await _post_json(EMBED, "/embeddings", {
        "model": config.EMBED_MODEL, "input": texts, "input_type": input_type, "truncate": "END"})
    return [d["embedding"] for d in sorted(out["data"], key=lambda d: d["index"])]


TTS_VOICES = {"hi": ("hi-IN", "Magpie-Multilingual.HI-IN.Aria"), "en": ("en-US", "Magpie-Multilingual.EN-US.Aria")}


async def tts(text: str, lang: str) -> bytes:
    if lang not in TTS_VOICES:
        raise NvError(f"tts: no voice for {lang}")
    TTS.acquire()
    code, voice = TTS_VOICES[lang]
    try:
        async with httpx.AsyncClient(timeout=config.HTTP_TIMEOUT_S * 2) as http:
            r = await http.post(config.TTS_URL, headers={"Authorization": f"Bearer {TTS.key}"},
                                data={"text": text[:800], "language": code, "voice": voice,
                                      "encoding": "LINEAR_PCM", "sample_rate_hz": "22050"})
    except httpx.HTTPError as e:
        raise TTS.fail(f"tts: {type(e).__name__}")
    if r.status_code != 200:
        raise TTS.fail(f"tts: HTTP {r.status_code}")
    return r.content


STT_CODES = {"hi": "hi-IN", "en": "en-US"}


def _stt_blocking(wav: bytes, lang: str) -> str:
    import riva.client  # heavy import, only when needed

    with wave.open(io.BytesIO(wav)) as w:
        rate, channels = w.getframerate(), w.getnchannels()
    auth = riva.client.Auth(None, True, config.STT_SERVER, [
        ["function-id", config.STT_FUNCTION_ID], ["authorization", f"Bearer {STT.key}"]])
    cfg = riva.client.RecognitionConfig(
        encoding=riva.client.AudioEncoding.LINEAR_PCM, sample_rate_hertz=rate,
        audio_channel_count=channels, language_code=STT_CODES.get(lang, "multi"),
        max_alternatives=1, enable_automatic_punctuation=True)
    resp = riva.client.ASRService(auth).offline_recognize(wav, cfg)
    return " ".join(r.alternatives[0].transcript.strip() for r in resp.results if r.alternatives).strip()


async def stt(wav: bytes, lang: str) -> str:
    STT.acquire()
    try:
        text = await asyncio.wait_for(asyncio.to_thread(_stt_blocking, wav, lang), config.HTTP_TIMEOUT_S * 2)
    except Exception as e:
        raise STT.fail(f"stt: {type(e).__name__} {str(e)[:80]}")
    if not text:
        raise STT.fail("stt: no speech recognised")
    return text
