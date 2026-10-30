import asyncio
import contextlib
import uuid
from typing import Literal

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from . import authority, db, drafts, gateway, llm, nv, payments, rag, voice


async def _reconciler():
    while True:
        await asyncio.sleep(3)
        with contextlib.suppress(Exception):
            payments.reconcile()


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    task = asyncio.create_task(_reconciler())
    yield
    task.cancel()


app = FastAPI(title="RTI Redesign API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"llm": llm.available(), "stt": nv.STT.configured, "tts": nv.TTS.configured,
            "bhashini": voice.bhashini_configured()}


@app.get("/usage")
def usage():
    """Calls made since the server started, per NVIDIA service, against our local throttle."""
    return {s.name: s.stats() for s in nv.ALL}


@app.get("/languages")
def languages():
    return {c: {"name": n, "quality": q} for c, (n, q) in voice.LANGUAGES.items()}


class SpeakIn(BaseModel):
    text: str
    lang: Literal["hi", "en"]


@app.post("/voice/speak")
async def speak(body: SpeakIn):
    try:
        wav = await nv.tts(body.text, body.lang)
    except nv.NvError as e:
        raise HTTPException(503, {"fallback": "browser-speech", "reason": str(e)})
    return Response(wav, media_type="audio/wav")


class AskIn(BaseModel):
    question: str
    lang: Literal["hi", "en"] = "en"


@app.post("/rag/ask")
async def rag_ask(body: AskIn):
    q = body.question.strip()
    if not q:
        raise HTTPException(400, "Ask a question")
    return await rag.ask(q[:500], body.lang)


# ---- applications -------------------------------------------------------
class NewApp(BaseModel):
    email: str


class DraftIn(BaseModel):
    draft: str
    source_lang: str = "en"
    original_text: str = ""


def _app_or_404(c, app_id: int):
    row = c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Application not found")
    return row


@app.post("/applications")
def create_application(body: NewApp):
    with db.tx() as c:
        cur = c.execute("INSERT INTO applications(email) VALUES (?)", (body.email,))
        db.log_event(c, cur.lastrowid, "CREATED")
        return dict(_app_or_404(c, cur.lastrowid))


@app.get("/applications")
def list_applications(email: str):
    with db.tx() as c:
        rows = c.execute("SELECT * FROM applications WHERE email=? ORDER BY id DESC", (email,))
        return [dict(r) for r in rows]


@app.get("/applications/{app_id}")
def get_application(app_id: int):
    with db.tx() as c:
        a = dict(_app_or_404(c, app_id))
        a["events"] = [dict(r) for r in c.execute(
            "SELECT kind, detail, at FROM events WHERE application_id=? ORDER BY id", (app_id,))]
        a["payments"] = [dict(r) for r in c.execute(
            "SELECT status, amount, created_at FROM payments WHERE application_id=? ORDER BY id",
            (app_id,))]
        return a


@app.put("/applications/{app_id}/draft")
def save_draft(app_id: int, body: DraftIn):
    """Autosave target. Accepts invalid text (user is mid-edit) but reports problems."""
    with db.tx() as c:
        a = _app_or_404(c, app_id)
        if a["state"] not in ("DRAFT", "PAYMENT_FAILED"):
            raise HTTPException(409, f"Cannot edit while {a['state']}")
        c.execute("UPDATE applications SET draft=?, source_lang=?, original_text=?, "
                  "updated_at=datetime('now') WHERE id=?",
                  (body.draft, body.source_lang, body.original_text, app_id))
    return drafts.validate(body.draft)


@app.post("/draft/validate")
def validate_draft(body: DraftIn):
    return drafts.validate(body.draft)


@app.post("/draft/sanitize")
def sanitize_draft(body: DraftIn):
    return {"draft": drafts.sanitize(body.draft)}


@app.post("/draft/refine")
async def refine(body: DraftIn):
    return {"draft": await voice.polish(body.draft, "en")}


# ---- authority ----------------------------------------------------------
class FindIn(BaseModel):
    text: str


@app.post("/authority/find")
async def find_authority(body: FindIn):
    return await authority.find(body.text)


@app.get("/authority/list")
def list_authorities():
    return [{"key": a.key, "name": a.name, "name_hi": authority.NAME_HI[a.key], "level": a.level}
            for a in authority.AUTHORITIES]


class ConfirmIn(BaseModel):
    authority_key: str


@app.post("/applications/{app_id}/authority")
def confirm_authority(app_id: int, body: ConfirmIn):
    if body.authority_key not in authority.BY_KEY:
        raise HTTPException(400, "Unknown authority")
    with db.tx() as c:
        _app_or_404(c, app_id)
        c.execute("UPDATE applications SET authority_key=?, authority_confirmed=1 WHERE id=?",
                  (body.authority_key, app_id))
        db.log_event(c, app_id, "AUTHORITY_CONFIRMED", body.authority_key)
    return {"ok": True}


# ---- voice --------------------------------------------------------------
@app.post("/voice/transcribe")
async def transcribe(audio: UploadFile = File(...), src: str = Form(...),
                     target: str = Form("en")):
    """Expects 16 kHz mono WAV (the frontend converts before upload)."""
    try:
        return await voice.transcribe_and_translate(await audio.read(), src, target)
    except voice.VoiceUnavailable as e:
        raise HTTPException(503, {"fallback": "browser-speech", "reason": str(e)})


class TranslateIn(BaseModel):
    text: str
    src: str
    target: Literal["en", "hi"] = "en"


@app.post("/voice/translate")
async def translate(body: TranslateIn):
    try:
        return await voice.translate_text(body.text, body.src, body.target)
    except voice.VoiceUnavailable as e:
        raise HTTPException(503, {"reason": str(e)})


# ---- payments -----------------------------------------------------------
class PayIn(BaseModel):
    scenario: Literal["success", "failure", "timeout"] = "success"


@app.post("/applications/{app_id}/pay")
def pay(app_id: int, body: PayIn, idempotency_key: str = Header(...)):
    try:
        return payments.pay(app_id, idempotency_key, body.scenario)
    except payments.PaymentError as e:
        raise HTTPException(e.code, str(e))


@app.post("/payments/reconcile")
def reconcile_now():
    return {"resolved": payments.reconcile()}


@app.post("/webhooks/gateway")
async def webhook(request: Request, x_signature: str = Header(...)):
    body = await request.body()
    import json
    data = json.loads(body or b"{}")
    try:
        payments.handle_webhook(body, x_signature, data.get("idem_key", ""), data.get("outcome", ""))
    except payments.PaymentError as e:
        raise HTTPException(e.code, str(e))
    return {"ok": True}
