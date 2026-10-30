import asyncio
import contextlib
import datetime as dt
import uuid
from typing import Literal

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from . import appeal, appeal_docs, attachments, authority, reminders, reply_review, db, drafts, gateway, llm, nv, payments, rag, voice


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
        a["children"] = [dict(r) for r in c.execute(
            "SELECT rti_number, note FROM children WHERE application_id=? ORDER BY id", (app_id,))]
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
def validate_draft(body: DraftIn, lang: Literal["en", "hi"] = "en"):
    return drafts.validate(body.draft, strict=lang == "en")


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


# ---- appeal -------------------------------------------------------------
class AppealIn(BaseModel):
    filed: dt.date
    replied: dt.date | None = None
    first_appeal: dt.date | None = None
    fa_decided: dt.date | None = None
    transferred_physically: bool = False
    today: dt.date | None = None  # for demos and tests


@app.post("/appeal/check")
def appeal_check(body: AppealIn):
    try:
        return appeal.assess(body.filed, body.today or dt.date.today(), body.replied, body.first_appeal,
                             body.fa_decided, body.transferred_physically)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---- appeal drafting and checks -----------------------------------------
class Free(BaseModel):
    model_config = {"extra": "allow"}
    today: dt.date | None = None


@app.get("/appeal/options")
def appeal_options():
    return {"grounds": appeal_docs.GROUNDS, "relief": appeal_docs.RELIEF,
            "docs": [{"code": c, "label": l, "mandatory": m} for c, l, m in appeal_docs.DOCS]}


@app.post("/appeal/first")
def appeal_first(body: Free):
    data = body.model_dump(exclude={"today"})
    return appeal_docs.first_appeal(data, body.today)


@app.post("/appeal/second")
def appeal_second(body: Free):
    data = body.model_dump(exclude={"today"})
    return appeal_docs.second_appeal(data, body.today)


class ReplyIn(BaseModel):
    text: str


@app.post("/reply/review")
def reply_review_endpoint(body: ReplyIn):
    return reply_review.review(body.text[:6000])


class AttachIn(BaseModel):
    filename: str
    size_bytes: int | None = None
    kind: Literal["supporting", "bpl"] = "supporting"


@app.post("/attachment/check")
def attachment_check(body: AttachIn):
    return attachments.check(body.filename, body.size_bytes, body.kind)


@app.post("/draft/analyze")
def draft_analyze(body: DraftIn):
    return {"hints": drafts.analyze_request(body.draft)}


@app.get("/applications/{app_id}/reminders")
def application_reminders(app_id: int, today: dt.date | None = None):
    with db.tx() as c:
        a = _app_or_404(c, app_id)
        ev = c.execute("SELECT at FROM events WHERE application_id=? AND kind='SUBMITTED'", (app_id,)).fetchone()
    if not ev:
        return {"submitted": None, "channel": "in-app (email and SMS are not connected in this demo)", "items": []}
    submitted = dt.date.fromisoformat(ev["at"][:10])
    return {"submitted": submitted.isoformat(), "channel": "in-app (email and SMS are not connected in this demo)",
            "items": reminders.for_request(submitted, today or dt.date.today())}


@app.post("/applications/{app_id}/demo-forward")
def demo_forward(app_id: int):
    """Demo only: pretend the request was forwarded to a second office, which gets its own number."""
    with db.tx() as c:
        a = _app_or_404(c, app_id)
        if not a["rti_number"]:
            raise HTTPException(409, "Submit the request first")
        n = c.execute("SELECT COUNT(*) FROM children WHERE application_id=?", (app_id,)).fetchone()[0]
        number = f"{a['rti_number']}/{chr(66 + n)}"
        c.execute("INSERT INTO children(application_id, rti_number, note) VALUES (?,?,?)",
                  (app_id, number, "Forwarded to another office (demo)"))
        db.log_event(c, app_id, "FORWARDED_DEMO", number)
    return {"rti_number": number}
