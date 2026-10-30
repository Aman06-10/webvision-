# RTI Portal Redesign: Plan

> Update: Bhashini was dropped from the project. Voice, translation and chat all use NVIDIA; Hindi and English are verified, other languages are beta. Mentions of Bhashini below are from the original plan and are kept for history.

Hackathon build, ~2.5 hours. Stack: Next.js (Tailwind, next-intl) + FastAPI + SQLite/Postgres.
LLM: NVIDIA API only (OpenAI-compatible). Voice: Bhashini (see decision D1).

---

## 1. All problems (consolidated)

| # | Problem | Technical term | Verified from portal text? |
|---|---|---|---|
| P1 | Wrong portal pe file, fee chali gayi | Pre-validation / routing logic | Yes (wrong-portal warning) |
| P2 | Paisa kata, RTI number nahi aaya; double payment ka risk; timeout pe "failed" | State machine, idempotency key, reconciliation, eventual consistency | Yes (payment FAQ) |
| P3 | 3000 char limit, invalid characters, draft loss | Client + server validation, sanitization, autosave | Yes |
| P4 | 22-language barrier: portal sirf English/Hindi | Vernacular voice, ASR + translation, i18n | Yes (problem statement) |
| P5 | Status / History / Login alag-alag | Single source of truth, unified data model | Partly |
| P6 | Status ke liye OTP delay | Rate limiting, resend throttling | Yes |
| P7 | Appeal button band, wajah nahi dikhti | Business rules engine | Needs check |
| P8 | CAPTCHA friction | WCAG 2.1 AA, GIGW 3.0, risk-based bot protection | Yes (text), **behaviour untested** |
| P9 | Mobile experience | Mobile-first, 44px touch targets | **Untested, claim mat kar** |
| P10 | Blinking GIFs, purana look | `prefers-reduced-motion` | Yes |
| P11 | Sensitive data | Audit logs, RBAC, TLS | Design-level |

---

## 2. Selection: what we build

Criteria: demo impact, buildable in 2.5h, verifiable, judge appeal (DPI, inclusion).

| Priority | Problem | Decision | Why |
|---|---|---|---|
| **Core 1** | P4 Vernacular voice | BUILD | Biggest inclusion story, Bhashini = DPI, strong live demo |
| **Core 2** | P1 Authority Finder | BUILD | Fixes the costliest user mistake; shows NVIDIA LLM + rule fallback |
| **Core 3** | P2 Payment state machine | BUILD | Strongest engineering depth; demoable with a mock gateway |
| Support | P3 Draft validation + autosave | BUILD (small) | Shares the draft editor with P4, almost free |
| Support | P5 Unified dashboard | BUILD (minimal) | One `applications` table, one list view; needed to show P2 states |
| Cheap win | P10 Static badge, reduced motion | BUILD (10 min) | CSS only |
| Stretch | P7 Appeal eligibility | Only if time left | Pure date logic |
| Slide only | P6 OTP, P11 security | Mention in architecture slide | Not demoable fast |
| Skip | P8 CAPTCHA, P9 mobile | Do NOT claim | Unverified; judges may ask for a demo |

The three core pieces form one story: **speak in your language -> draft in English/Hindi -> right authority -> payment that never loses your money.**

---

## 3. Decisions to confirm

**D1. Bhashini vs "sirf NVIDIA".**
The brief for P4 says use Bhashini (ASR + translation). Earlier we decided NVIDIA only for the LLM. These do not conflict if split by job:
- Bhashini: speech-to-text and translation (the DPI piece).
- NVIDIA LLM: authority classification and draft polishing.
- Fallback for the mic if Bhashini keys/endpoint are not ready: browser Web Speech API (Chrome sends audio to Google; tell judges).

Action before building: register on the Bhashini developer portal and get API credentials. I have not verified the current endpoint names or request format, so read their current docs rather than trusting any snippet from memory. Registration approval can take time, so start it first.

**D2. Gateway.** Real payment gateway is out of scope. Use a mock gateway that can simulate success, failure, timeout and delayed webhook.

---

## 4. Architecture

```
Next.js frontend (next-intl, Tailwind)
  |  mic audio / text
  v
FastAPI backend  (all keys live here, .env only)
  |-- /voice/transcribe  -> Bhashini ASR -> regional text
  |-- /voice/translate   -> Bhashini NMT -> English/Hindi draft
  |-- /draft/refine      -> NVIDIA LLM (polish into formal RTI wording)
  |-- /authority/find    -> rules first, NVIDIA LLM second, rules as fallback
  |-- /payments/*        -> state machine + mock gateway + reconciliation job
  |-- /applications      -> unified list for dashboard
  v
DB: applications, payments, payment_events, audit_log
```

Rules:
- API keys only in backend `.env`. Never in frontend or git (`.env` in `.gitignore`).
- Every external call has a timeout and a fallback so the demo never dead-ends.

---

## 5. Feature specs

### 5.1 Voice to official draft (P4)

Flow:
1. User picks language (or auto-detect) and presses mic.
2. Audio goes to backend -> Bhashini ASR -> regional text shown live.
3. Backend translates to English (or Hindi) via Bhashini translation.
4. NVIDIA LLM rewrites into formal RTI language. Prompt must keep facts unchanged and never invent names, dates or amounts.
5. User sees **both** original text and official draft side by side, edits, then continues.

Requirements:
- Always show the original-language text next to the translation so the user can verify what was filed in their name.
- Draft goes into the same editor as P3 (counter, autosave).
- Start with 4-5 demo languages (Hindi, Tamil, Bengali, Marathi, Telugu), design for all 22 via a language config list.
- Fallbacks: Bhashini fails -> Web Speech API; LLM fails -> show plain translation without polishing.

Acceptance: speak one sentence in a regional language -> official English draft in under ~10s on demo network.

### 5.2 Authority Finder (P1)

Flow: user describes the information needed -> system suggests the public authority / portal **before payment**.
- Step 1, rules: keyword map (railways, income tax, state police, municipal, etc.) to central vs state portal.
- Step 2, NVIDIA LLM: used when rules give low confidence. Returns JSON `{authority, portal, confidence, reason}`.
- Step 3, fallback: if LLM times out or rate-limits, return the rules result with a "please confirm" prompt.
- Show reason + confidence; user can override. Block payment step until user confirms the authority.

Acceptance: 10 hand-written test queries, rule-only mode still returns a sensible answer for each obvious one.

### 5.3 Payment state machine (P2)

States: `DRAFT -> PAYMENT_INITIATED -> PAYMENT_PENDING -> PAID -> SUBMITTED` plus `PAYMENT_FAILED`.
(`PAYMENT_PENDING` is the key one: it means "gateway has not confirmed yet", never shown as "Failed".)

Rules:
- Each payment attempt has a unique idempotency key. Replaying the same request returns the same result.
- DB unique constraint: one active payment per application.
- Timeout from gateway = `PAYMENT_PENDING`, not failed.
- Webhook handler verifies signature (mock secret) and is idempotent.
- Reconciliation job (background task, every N seconds) asks the gateway for status of every pending payment and resolves it.
- Every transition writes a row to `payment_events` (audit trail).
- RTI number is generated only on `PAID -> SUBMITTED`, so "money cut, no number" becomes a visible, self-healing state.

Demo script: click Pay with "simulate timeout" -> UI shows "Confirming your payment" -> reconciliation resolves it -> number appears. Then double-click Pay to show no double charge.

### 5.4 Draft editor (P3, small)
- Live counter (x / 3000), warning at 90%.
- Highlight invalid characters, with a one-click "remove" action. Validate on both client and server.
- Autosave to backend every few seconds and on blur; restore on reload.

### 5.5 Unified dashboard (P5, minimal)
- One `applications` table and one list page: status, payment state, RTI number.
- Guest lookup by email-verified link (stretch; skip if short on time).

### 5.6 Quick wins (P10)
- Replace blinking GIFs with a static badge; wrap any animation in `prefers-reduced-motion`.

---

## 6. Time plan (2.5h)

| Time | Task |
|---|---|
| 0:00-0:15 | Scaffold Next.js + FastAPI, `.env`, DB models, language config |
| 0:15-0:55 | Voice pipeline (Bhashini ASR + translation, Web Speech fallback) + draft editor |
| 0:55-1:20 | Authority Finder (rules, then NVIDIA, then fallback) |
| 1:20-2:05 | Payment state machine, mock gateway, reconciliation, events |
| 2:05-2:20 | Dashboard list + P10 quick wins |
| 2:20-2:30 | Demo rehearsal, README, slide notes |

If behind schedule, cut in this order: dashboard guest lookup, P10, LLM polish step. Never cut fallbacks.

---

## 7. Honesty checklist for judges

- Claim only what is verified from portal text: wrong-portal warning, payment FAQ, 3000-char limit, OTP delay, CAPTCHA text, blinking GIF.
- Do **not** claim mobile bugs or CAPTCHA malfunction unless tested by hand.
- Say clearly: which parts are mocked (payment gateway), which use Google (Web Speech fallback), which use Bhashini, which use NVIDIA.
- Do not claim the portal has "no" multilingual support beyond what you checked; say it "heavily favours English and Hindi" as the problem statement does.

---

## 8. Next step

Starter code order: (1) FastAPI skeleton + NVIDIA client with timeout/fallback, (2) Authority Finder, (3) payment state machine with tests, (4) voice endpoints once Bhashini credentials are in hand.
