# RTI Filing, Redesigned

A redesign concept for the online RTI (Right to Information) filing experience. It fixes the points where citizens lose time or money: filing with the wrong authority, payments that are cut without an RTI number, an unforgiving text box, and an interface that favours English and Hindi.

> **This is a concept built for a hackathon. It is not the official portal and does not file real RTI requests.** Payments go through a mock gateway.

## What it does

| Problem on the current portal | What this project does |
|---|---|
| Hard to write a request in your own language | Speak or type in your language; get an official English or Hindi draft, shown next to your original words |
| Filing with the wrong authority can cost the fee | Suggests the right authority and portal before payment, with a confidence level and the reason. Unsure cases show the closest options to pick from instead of a forced guess |
| Money cut, no RTI number | Payment state machine. A bank timeout shows **Confirming**, never **Failed**. The app checks with the bank on its own and issues the number once confirmed |
| Double payment risk | Idempotency key per attempt plus a database rule: one live payment per request |
| 3000-character limit and invalid characters | Live counter, invalid characters listed with one-click removal, server-side validation, autosave |
| Hard to understand fees, deadlines, appeals | Help assistant that answers only from a small RTI knowledge base and cites its sources |
| Hard for people who read slowly or not at all | "Listen" button reads the draft and the RTI number aloud (Hindi and English) |

Interface is available in English and Hindi. Animations respect `prefers-reduced-motion`.

## Architecture

```
React + Vite frontend (hand-written CSS, English/Hindi UI)
        |  /api proxy
FastAPI backend  (all API keys live here, never in the browser)
  |- /voice/transcribe   NVIDIA Parakeet speech-to-text -> translate
  |- /voice/translate    NVIDIA Riva translate (hi<->en), chat-model fallback
  |- /voice/speak        NVIDIA Magpie text-to-speech (hi, en)
  |- /draft/*            validate, sanitize, tidy wording (chat model)
  |- /authority/find     keyword rules (English, Hindi, Hinglish) -> embeddings -> chat model among the closest candidates -> "unknown"
  |- /rag/ask            embeddings search -> chat model answers from the knowledge base
  |- /applications/*     drafts, authority confirmation, payment
  |- /payments/*         state machine, mock gateway, webhook, reconciliation
  |- /usage              calls per NVIDIA service vs local throttle
SQLite: applications, payments (unique active-payment index), events (audit trail)
```

Every external call has a timeout and a fallback, so the flow never dead-ends if an API is slow or down.

### Payment states

```
Application: DRAFT -> PAYMENT_PENDING -> SUBMITTED
                         \-> PAYMENT_FAILED -> (retry with a new key)
Payment:     INITIATED -> PENDING -> PAID | FAILED
```

The RTI number is created only on `PAID -> SUBMITTED`. A background reconciler resolves `PENDING` payments; webhooks are signature-checked and idempotent.

## Run it locally

Requirements: Python 3.11+ and Node 18+.

```bash
# backend
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your NVIDIA keys
uvicorn app.main:app --port 8001
```

```bash
# frontend (new terminal)
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

The frontend proxies `/api` to `http://localhost:8001` (see `frontend/vite.config.ts`).

### Environment

Create the keys at [build.nvidia.com](https://build.nvidia.com). `backend/.env` is git-ignored; never commit it or put keys in the frontend.

| Variable | Used for |
|---|---|
| `NVIDIA_KEY_RAG` | Chat model: help answers, wording tidy, fallback translation |
| `NVIDIA_KEY_EMBED` | Embeddings for the help assistant |
| `NVIDIA_KEY_TRANSLATE` | Riva translate (Hindi and English) |
| `NVIDIA_KEY_TTS` | Text-to-speech |
| `NVIDIA_KEY_STT` | Speech-to-text |
| `NVIDIA_RPM_LIMIT` | Local per-service throttle (default 35 per minute) |
| `NVIDIA_CHAT_MODEL`, `NVIDIA_EMBED_MODEL`, `NVIDIA_TRANSLATE_MODEL` | Override models. NVIDIA retires models, so check the catalog if a call returns 404 or 410 |

Without any keys the app still works: authority finding falls back to keyword rules, translation and voice report that they are unavailable, and the browser's own speech recognition can be used for the mic.

### Tests

```bash
cd backend && . .venv/bin/activate && python -m pytest -q
```

Covers the payment state machine (replay, double payment, timeout then reconcile, failure then retry, webhook signature), authority rules and fallbacks, draft validation, the rate limiter, and the help assistant's fallbacks.

## Try the demo

1. Enter an email and start a request.
2. Speak or type in your language, then **Prepare official draft**. Hindi and English are verified; other languages show a *beta* warning.
3. Continue: the authority is suggested automatically. Confirm it.
4. On the last step, use the **Demo only** box to simulate the bank:
   - *Bank does not respond*: status stays **Confirming**, then resolves to **Submitted** on its own after about 8 seconds.
   - *Bank declines*: shows **not completed, no money taken**, and you can retry.
   - Press Pay twice quickly: only one payment is created.
5. Open **Help** and ask, for example, "My payment was cut but I have no number".

## What is verified and what is not

Checked end to end against the live NVIDIA APIs on 2026-10-30:

- Speech-to-text, text-to-speech, and Hindi to English and English to Hindi translation (round trip with a synthesized Hindi sentence).
- Embeddings and chat. Help answers are grounded; unrelated questions are refused without calling the chat model.
- Full browser flow: draft, authority, timeout payment with reconciliation, RTI number, Hindi interface, mobile width.

Known limits, stated plainly:

- **Only Hindi and English are verified for voice and translation.** In testing, Tamil, Telugu, Marathi and Gujarati text was mistranslated by the Riva translate model, and the chat model also made mistakes. Those languages are marked *beta* and the user is asked to review the English text. Reaching all 22 scheduled languages needs a dedicated service such as Bhashini; an optional adapter is in `backend/app/voice.py` but is **untested** (no credentials).
- Text-to-speech has Hindi and English voices only; other languages fall back to the browser voice.
- The mic button in the browser was not tested by a person; the backend path was tested with a WAV file.
- The knowledge base in `backend/app/kb.py` is general guidance from the RTI Act, 2005 and the central RTI Rules, 2012 as the author understands them. State rules differ. It is not legal advice; verify before relying on any figure.
- **Authority detection accuracy** (22 demo authorities, live APIs): 26 of 26 on the set the keyword lists were tuned on (so optimistic), and 17 of 18 on a held-out set of paraphrases written afterwards with no keywords in mind. The one miss (road tarring in a colony, chose PWD over municipal) came back with 0.6 confidence and municipal as an alternative. Queries are in `backend/tests/queries.py`; the held-out set is small, so treat this as indicative. Vague text such as "help" returns unknown and asks for more detail.
- The authority table is demo data, and the allowed-character set for drafts is an assumption. Replace both with the real directory and the portal's actual rules.
- Claims about the current portal's wrong-portal warning, payment FAQ, 3000-character limit, OTP delay, CAPTCHA text and blinking GIFs come from the portal's text. Mobile behaviour and CAPTCHA malfunction were **not** tested and are not claimed.

### NVIDIA usage limits

Hosted models on build.nvidia.com are a trial service. Reports commonly cite about 40 requests per minute per account, but NVIDIA says limits vary by model, and responses carry no rate-limit headers, so remaining quota is not visible from the API; check your profile on build.nvidia.com. The backend throttles itself to 35 per minute per service and exposes counters at `GET /usage`.

## Project layout

```
backend/
  app/
    main.py        API routes
    nv.py          NVIDIA client: chat, translate, embed, TTS, STT, rate limiter
    voice.py       language list, translation routing, wording tidy
    rag.py, kb.py  help assistant and its knowledge base
    authority.py   authority finder (rules, then chat model)
    payments.py    state machine, reconciliation, webhook
    gateway.py     mock payment gateway
    drafts.py      validation and sanitising
    db.py          SQLite schema
  tests/
frontend/
  src/
    App.tsx, RequestFlow.tsx, Help.tsx, Dashboard.tsx
    i18n.ts        English and Hindi strings
    audio.ts       recording, WAV conversion, speech helpers
    styles.css     design and animations
REDESIGN_PLAN.md   original problem selection and plan
```

## Design notes

Navy and white with a single saffron accent, a step sidebar (Speak, Office, Pay), 44px touch targets, visible focus rings, `aria-live` status messages, and a labelled mic. Animations (progress line, voice waveform, typed-out draft, payment timeline) are decorative and switch off with reduced-motion.
