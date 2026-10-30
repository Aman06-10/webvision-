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
| 3000-character limit and a narrow character set | Live counter, disallowed characters listed with one-tap auto-fix (the real portal set), Hindi or over-long drafts flagged as PDF attachments, autosave |
| Hard to understand fees, deadlines, appeals | Help assistant that answers only from a small RTI knowledge base and cites its sources |
| The first appeal will not open and nobody says why | Appeal checker: open or closed, the reason, and the dates (reply due, appeal window, second appeal) |
| Second appeals are returned for format defects | Second-appeal drafter built on the CIC's own format (RTI Rules 2012, Rule 8) with a checklist of what the Commission calls mandatory, late-appeal and condonation checks |
| A refusal that cites a section nobody explains | "Understand a reply": which section is cited, what it covers, usual grounds, and whether reasons and appeal rights were stated; one tap carries the grounds into a first-appeal draft |
| Requests worded as questions get refused | Hints while writing: ask for records, no Aadhaar or PAN numbers |
| Payments fail for avoidable reasons | "Before you pay" checklist from the portal's own list of failure reasons, plus an attachment-name checker (no spaces, no identity documents) |
| No reminders as deadlines approach | Reminders panel with the dates already worked out (shown in-app only; email and SMS are not connected) |
| Not sure what to write | Ten starter requests (ration card, roads, PF, pension, electricity, police, water, land, hospital, passport) in English and Hindi that ask for records |
| Bright screens are hard on the eyes at night | Dark mode: follows the system setting until you pick one with the header toggle; text contrast was checked on every page |
| Small text is hard to read | Text size controls (A-, A, A+) in the header, remembered between visits |
| Records kept only 3 years | Receipt download and print-to-PDF |
| Hard for people who read slowly or not at all | "Listen" button reads the draft and the RTI number aloud (Hindi and English) |

Interface is available in English and Hindi. Motion (scroll reveal, count-up figures, typed draft, payment timeline, a short confetti burst on submit) is decorative and switches off with `prefers-reduced-motion`.

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
  |- /appeal/check       appeal eligibility and dates (pure rules, no AI)
  |- /appeal/first, /appeal/second   draft and check appeals (templates and rules, no AI)
  |- /reply/review      explain the section a reply cites (rules)
  |- /draft/analyze, /attachment/check   wording hints, attachment name check
  |- /applications/{id}/reminders   deadline reminders
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

Covers appeal rules (every stage and boundary day), the payment state machine (replay, double payment, timeout then reconcile, failure then retry, webhook signature), authority rules and fallbacks, draft validation, the rate limiter, and the help assistant's fallbacks.

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

- **Only Hindi and English are verified for voice and translation.** In testing, Tamil, Telugu, Marathi and Gujarati text was mistranslated by the Riva translate model, and the chat model also made mistakes. Those languages are marked *beta* and the user is asked to review the English text. Reaching all 22 scheduled languages would need a dedicated language service; that is not part of this project.
- Text-to-speech has Hindi and English voices only; other languages fall back to the browser voice.
- The mic button in the browser was not tested by a person; the backend path was tested with a WAV file.
- The knowledge base in `backend/app/kb.py` is general guidance from the RTI Act, 2005 and the central RTI Rules, 2012 as the author understands them. State rules differ. It is not legal advice; verify before relying on any figure.
- **Authority detection accuracy** (22 demo authorities, live APIs): 26 of 26 on the set the keyword lists were tuned on (so optimistic), and 17 of 18 on a held-out set of paraphrases written afterwards with no keywords in mind. The one miss (road tarring in a colony, chose PWD over municipal) came back with 0.6 confidence and municipal as an alternative. Queries are in `backend/tests/queries.py`; the held-out set is small, so treat this as indicative. Vague text such as "help" returns unknown and asks for more detail.
- The authority table is demo data; replace it with the real directory. The draft character rule and the facts on the landing page were read from rtionline.gov.in (Guidelines and FAQ) on 2026-10-30 and may change.
- Appeal dates follow the RTI Act and, for second appeals, the Central Information Commission's own guidelines (30-day reply; 30-day first appeal window; second appeal after the first appeal is decided or 45 days have passed, within 90 days). They are covered by unit tests. The second-appeal format and checklist come from cic.gov.in pages read on 2026-10-30; the Commission can still return an appeal, and whether the checker reduces returns is a hypothesis, not a measured result. The first-appeal draft is a convenience: the portal has no prescribed first-appeal format. A late appeal can still be admitted for good reason; the checker does not judge that. Not legal advice.
- Claims about the current portal's wrong-portal warning, payment FAQ, 3000-character limit, OTP delay, CAPTCHA text and blinking GIFs come from the portal's text. Mobile behaviour and CAPTCHA malfunction were **not** tested and are not claimed.

### NVIDIA usage limits

Hosted models on build.nvidia.com are a trial service. Reports commonly cite about 40 requests per minute per account, but NVIDIA says limits vary by model, and responses carry no rate-limit headers, so remaining quota is not visible from the API; check your profile on build.nvidia.com. The backend throttles itself to 35 per minute per service and exposes counters at `GET /usage`.

## More problems the portal's own FAQ points to

Taken from the 26-question FAQ on rtionline.gov.in, as candidates for the next redesign steps (none are built yet unless marked):

- Payment fails for seven listed reasons (card e-commerce flag off, session timeout, wrong OTP, wrong card details, low balance, switching payment mode, UPI request not approved). *Built: retry screen and a pre-payment checklist.*
- Reconciliation takes 24 to 48 working hours and users are told to email a helpline. A status page with a "what to do now" step would replace the email. *Partly built (Confirming state).*
- One request can produce several registration numbers when it is forwarded to several CPIOs. *Grouped view built, but only a demo button simulates the forwarding.*
- A "supporting documents required" alert is only found by opening View Status; surface it on the dashboard.
- Manually filed applications cannot get an online first appeal unless the CPIO lodges them; explain this up front. *Explained in the appeal checker's transfer case.*
- The status OTP goes by email and can be delayed; add a resend cooldown and delivery hint.
- Requests are kept for 3 years only. *Receipt download and print built.*
- The FAQ advises users to ignore a browser certificate error. If that is still current, it trains users to bypass security warnings and should be fixed at the source.
- The text box accepts English only; the real fix is an official way to submit text in Indian languages.

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
    appeal.py      appeal eligibility rules and dates
    drafts.py      real portal character rules, validation and auto-fix
    db.py          SQLite schema
  tests/
frontend/
  src/
    App.tsx, Home.tsx (landing), RequestFlow.tsx, Appeal.tsx, Help.tsx, Dashboard.tsx
    i18n.ts, strings2.ts   English and Hindi strings
    audio.ts       recording, WAV conversion, speech helpers
    styles.css     design and animations
REDESIGN_PLAN.md   original problem selection and plan
```

## Design notes

Navy and white with a single saffron accent, a step sidebar (Speak, Office, Pay), 44px touch targets, visible focus rings, `aria-live` status messages, and a labelled mic. Animations (progress line, voice waveform, typed-out draft, payment timeline) are decorative and switch off with reduced-motion.
