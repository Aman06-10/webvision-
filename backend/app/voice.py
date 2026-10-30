"""Voice -> text -> official English/Hindi draft (NVIDIA speech + translate; Bhashini optional).

Bhashini path follows the ULCA "pipeline" flow as I understand it
(config call with userID + ulcaApiKey, then compute call to the returned
callback URL). It is UNTESTED without credentials: verify against the
current Bhashini docs. Any failure raises VoiceUnavailable so the caller can
fall back (browser speech for ASR, NVIDIA LLM for translation).
"""
import base64

import httpx

from . import config, llm, nv

# code -> (native name, quality). Only hi and en have been checked end to end with
# NVIDIA speech + translation. Others work through a general chat model and can
# mistranslate (tested: Tamil, Telugu, Marathi, Gujarati came back wrong), so the
# UI warns and asks the user to review.
LANGUAGES = {
    "hi": ("हिन्दी", "verified"), "en": ("English", "verified"),
    "bn": ("বাংলা", "beta"), "ta": ("தமிழ்", "beta"), "te": ("తెలుగు", "beta"),
    "mr": ("मराठी", "beta"), "gu": ("ગુજરાતી", "beta"), "kn": ("ಕನ್ನಡ", "beta"),
    "ml": ("മലയാളം", "beta"), "pa": ("ਪੰਜਾਬੀ", "beta"), "or": ("ଓଡ଼ିଆ", "beta"),
    "as": ("অসমীয়া", "beta"), "ur": ("اردو", "beta"),
}
VERIFIED = {c for c, (_, q) in LANGUAGES.items() if q == "verified"}
ENGLISH_NAMES = {
    "hi": "Hindi", "en": "English", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
    "pa": "Punjabi", "or": "Odia", "as": "Assamese", "ur": "Urdu",
}


class VoiceUnavailable(Exception):
    pass


def bhashini_configured() -> bool:
    return bool(config.BHASHINI_USER_ID and config.BHASHINI_ULCA_API_KEY)


async def _pipeline(tasks: list[dict], input_data: dict) -> dict:
    if not bhashini_configured():
        raise VoiceUnavailable("Bhashini not configured")
    try:
        async with httpx.AsyncClient(timeout=20) as http:
            cfg = await http.post(
                config.BHASHINI_CONFIG_URL,
                headers={"userID": config.BHASHINI_USER_ID,
                         "ulcaApiKey": config.BHASHINI_ULCA_API_KEY},
                json={"pipelineTasks": [{"taskType": t["taskType"], "config": {
                    "language": t["config"]["language"]}} for t in tasks],
                    "pipelineRequestConfig": {"pipelineId": config.BHASHINI_PIPELINE_ID}},
            )
            cfg.raise_for_status()
            cfg = cfg.json()
            ep = cfg["pipelineInferenceAPIEndPoint"]
            by_task = {c["taskType"]: c["config"][0]["serviceId"]
                       for c in cfg["pipelineResponseConfig"]}
            for t in tasks:
                t["config"]["serviceId"] = by_task[t["taskType"]]
            r = await http.post(
                ep["callbackUrl"],
                headers={ep["inferenceApiKey"]["name"]: ep["inferenceApiKey"]["value"]},
                json={"pipelineTasks": tasks, "inputData": input_data},
            )
            r.raise_for_status()
            return r.json()
    except VoiceUnavailable:
        raise
    except Exception as e:
        raise VoiceUnavailable(f"Bhashini call failed: {e}") from e


async def transcribe_and_translate(wav: bytes, src: str, target: str) -> dict:
    """wav = 16 kHz mono PCM. NVIDIA speech-to-text, then translation."""
    if src not in VERIFIED and bhashini_configured():
        try:
            return await _bhashini_asr_translate(wav, src, target)
        except VoiceUnavailable:
            pass  # fall back to NVIDIA below
    try:
        original = await nv.stt(wav, src)
    except nv.NvError as e:
        raise VoiceUnavailable(str(e)) from e
    out = await translate_text(original, src, target)
    return {**out, "original": original, "engine": "nvidia-riva+" + out["engine"]}


async def _bhashini_asr_translate(wav: bytes, src: str, target: str) -> dict:
    tasks = [{"taskType": "asr", "config": {"language": {"sourceLanguage": src},
                                            "audioFormat": "wav", "samplingRate": 16000}},
             {"taskType": "translation", "config": {"language": {"sourceLanguage": src, "targetLanguage": target}}}]
    out = await _pipeline(tasks, {"audio": [{"audioContent": base64.b64encode(wav).decode()}]})
    try:
        by = {r["taskType"]: r["output"][0] for r in out["pipelineResponse"]}
        return {"original": by["asr"]["source"], "translated": by["translation"]["target"],
                "engine": "bhashini", "quality": "beta"}
    except (KeyError, IndexError) as e:
        raise VoiceUnavailable("Unexpected Bhashini response") from e


async def translate_text(text: str, src: str, target: str) -> dict:
    """Returns {original, translated, engine, quality}. quality is 'verified' or 'beta'."""
    if src == target:
        return {"original": text, "translated": text, "engine": "none", "quality": "verified"}
    quality = "verified" if src in VERIFIED and target in VERIFIED else "beta"

    if quality == "verified":
        try:
            return {"original": text, "translated": await nv.translate(text, src, target),
                    "engine": "nvidia-riva-translate", "quality": "verified"}
        except nv.NvError:
            quality = "beta"  # fall through to other engines, flagged as unverified

    if bhashini_configured():
        try:
            out = await _pipeline(
                [{"taskType": "translation", "config": {
                    "language": {"sourceLanguage": src, "targetLanguage": target}}}],
                {"input": [{"source": text}]})
            return {"original": text, "translated": out["pipelineResponse"][0]["output"][0]["target"],
                    "engine": "bhashini", "quality": "beta"}
        except (VoiceUnavailable, KeyError, IndexError):
            pass

    t = await llm.chat(
        "You are a careful translator.",
        f"Translate the following {ENGLISH_NAMES.get(src, src)} text into "
        f"{ENGLISH_NAMES.get(target, target)}. Keep every fact. Output only the translation.\n\n{text}",
        temperature=0)
    if not t:
        raise VoiceUnavailable("No translation engine available")
    return {"original": text, "translated": t, "engine": "nvidia-chat", "quality": "beta"}


async def polish(text: str, lang: str) -> str:
    """Tidy a request into clear, formal RTI wording. Falls back to the input."""
    out = await llm.chat(
        "You edit citizen requests for Indian RTI applications.",
        f"Rewrite the request below in clear, formal {ENGLISH_NAMES.get(lang, 'English')}. "
        "Output ONLY the body of the request: no heading, no 'To/Subject' lines, no greeting or sign-off, "
        "no mention of fees, and no placeholders in brackets. Keep every fact exactly as given and do not "
        "add names, dates, places, amounts or anything the citizen did not say. If there are several "
        f"questions, number them.\n\nRequest:\n{text}", temperature=0.2)
    return out or text
