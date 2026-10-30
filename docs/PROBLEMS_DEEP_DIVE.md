# RTI in India: where it breaks, and what this project does and does not fix

Research notes, 30 October 2026. Evidence is graded: **[portal]** read directly on rtionline.gov.in, **[report]** from a published report or news story, **[claim]** a quoted opinion, **[unverified]** could not be checked. Figures from different sources use different definitions and dates; do not mix them in a pitch without saying so. Nothing here is legal advice.

## 1. How an RTI actually travels

1. Citizen files on **rtionline.gov.in** (central bodies only) or on a state portal or on paper. [portal]
2. The request reaches the department's **Nodal Officer**, not the CPIO. The Nodal Officer forwards it, or transfers it (Section 6(3)) if the wrong body was picked. [portal]
3. The CPIO should reply within **30 days**. A request can fan out to several CPIOs and produce several registration numbers. [portal]
4. Unhappy or no reply: **first appeal** to the First Appellate Authority. Free. Online only if the original was filed online, and only after the 30 days have passed if there was no reply. [portal]
5. Still unhappy: **second appeal or complaint** to the Central or State Information Commission within 90 days. The portal footer sends you to a separate "Complaint and Second Appeal to CIC" system. [portal]
6. Commissions have backlogs, vacancies and format rules. [report]

## 2. Problems by stage, and where this project stands

Status: **Built** (works in the demo), **Partly**, **Not built**, **Not ours** (law, staffing or policy; software cannot fix it).

### Before filing

| Problem | Evidence | Status |
|---|---|---|
| Text box takes English only, 3000 characters, 14 symbols | [portal] guidelines | **Built**: Hindi/English voice drafting, rule checker, auto-fix, PDF attachment flag. The portal itself is unchanged, so Hindi text still goes in as a PDF |
| Central vs state confusion; wrong filing returned **with no refund** | [portal] FAQ | **Built**: office finder, state warning (demo list of 22 offices) |
| Do not know how to word a request; vague or question-style requests get refused | [report] commentary and Goa SIC case; one outlet says ~30% of applications are rejected for being in question form, **[unverified]** | **Built**: hints flag question-style requests and ID numbers |
| Low awareness in rural areas, women, SC, ST, OBC | [report] PRIA study: ~21% of applications from rural applicants, but only one state (Chhattisgarh) records it | **Partly**: voice and Hindi help; no outreach or assisted mode |
| Indian-language access | [report] portal is Hindi and English only; parliamentary document asks for regional-language options | **Partly**: Hindi and English verified, others beta |

### Filing and payment

| Problem | Evidence | Status |
|---|---|---|
| Money cut, no registration number; told to wait 24 to 48 working hours | [portal] | **Built**: Confirming state, auto-reconcile, double-payment block (mock gateway) |
| Seven listed reasons payments fail | [portal] FAQ | **Built**: clear failed screen and pre-payment checklist |
| Attachment rules: PDF name must have no spaces; do not upload Aadhaar or PAN; BPL certificate only | [portal] | **Built (name only)**: checks file name and identity-document names; size limit not stated in the guidelines |
| Portal technical trouble and slow responses | [report] a notice on the portal's registration page, seen via search; **[unverified]** date | **Not ours** |

### After filing (the 30-day black box)

| Problem | Evidence | Status |
|---|---|---|
| Status needs registration number, email, CAPTCHA and an OTP; OTP email can be delayed | [portal] | **Not built** (no resend cooldown or delivery hint) |
| Extra-fee demands and "supporting documents required" alerts live inside View Status | [portal] FAQ | **Not built** |
| Several registration numbers for one request | [portal] FAQ | **Partly**: grouped view built; forwarding is simulated |
| No reminders as deadlines approach | inferred | **Partly**: reminders with computed dates; in-app only, no email or SMS |
| Cases kept only 3 years | [portal] FAQ | **Built**: receipt download and print |

### Reply and first appeal

| Problem | Evidence | Status |
|---|---|---|
| Exemptions used heavily; Section 8(1)(j) (personal information) most invoked | [report] CIC annual reports 2019-20; CHRI study of 10 commissions found about 10% of queries rejected, with large variation | **Built (v1)**: explains the clause cited and usual grounds; does not judge lawfulness |
| Rejections under an unexplained "others" category | [report] CIC data for 2015-16: 43% of rejections; old data | **Not ours**, but a reply reviewer could flag it |
| First appeal will not open and the reason is buried | [portal] FAQ | **Built**: appeal checker with reasons and dates |
| Manual applications cannot be appealed online unless a CPIO lodges them | [portal] FAQ | **Partly**: transfer case explained |
| Writing a first appeal | inferred | **Built**: first-appeal draft from standard grounds |

### Second appeal and the commissions

| Problem | Evidence | Status |
|---|---|---|
| **Cases returned without orders for format defects.** CIC returned 14,603 cases from July 2025 to June 2026 against 31,179 registered; nine commissions returned 37,701. Commissions return appeals that do not follow prescribed formats; one campaigner cites missing page numbers. About 95% of CIC returns were reportedly never re-filed | [report] PTI story on the SNS report, 13 Oct 2026; the 95% is from earlier data cited there. Returned and registered may not count the same things | **Built (v1)**: second-appeal drafter and checker on the CIC's published format and checklist. Unproven that it prevents returns |
| Backlog: about 3.85 lakh appeals and complaints pending in 28 commissions on 30 June 2026; CIC pendency reported up by 9,378 between 1 Jan and 12 Oct 2026 | [report] SNS via PTI; [claim] the 9,378 is one retired officer's statement | **Not ours** |
| Very long waits: 14 commissions may take a year or more; the report estimates 19 years 8 months for Tripura | [report] SNS via PTI | **Not ours**, but the app could show expected wait up front |
| Penalties rarely imposed on PIOs | [report] SNS editions give figures between about 4% and 9% of eligible cases; editions differ, check the year before quoting | **Not ours** |

### Law, safety and trust

| Problem | Evidence | Status |
|---|---|---|
| DPDP Act Section 44(3) replaces RTI Section 8(1)(j) and removes the public-interest override for personal information; challenged in the Supreme Court; sources disagree on whether and when it is in force | [report] several outlets | **Not ours**; the Help assistant should say it is contested |
| Attacks on RTI users: CHRI counts at least 107 killed; Maharashtra and Gujarat lead | [report] CHRI as cited by media | **Not ours**; design implication is to collect and show the minimum personal data |
| The FAQ tells users to ignore a browser certificate error | [portal] FAQ text as read; may be outdated | **Not ours**; raise at the source |
| Third-party sites give confident payment-refund advice that cannot be verified | [unverified] | Use official text only |

## 3. Second-appeal rules read from the CIC (new)

From cic.gov.in Second Appeal Guidelines and FAQ, read 30 Oct 2026: mandatory are a signed appeal, a copy of the RTI application and a copy of the first appeal, all related, legible and in Hindi or English; if available, the reply, the first appeal order, other relied documents and an index; all signed or self-attested; one copy with proof of service on the CPIO and FAA; no fee; a second appeal without a first appeal is liable to be returned; a late appeal needs a formal condonation request or is liable to be rejected. Timing: file after the first appeal is decided or 45 days after it, within 90 days. Help desk 011-26183053, fdesk-cic[at]gov[dot]in. The format is Rule 8 of the RTI Rules, 2012 (eleven items). Third-party sites disagree on upload limits and extra forms; none of those are used here.

## 4. What to build next, ranked

1. **Appeal drafter and format checker** (first and second appeal). Evidence is the 14,603 returned CIC cases. Build: form with required fields and page-number checks, plain-language grounds, PDF-ready output. Risk: formats differ by commission; verify against the CIC's current prescribed format before claiming compliance.
2. **Reply reviewer.** Paste or upload the reply; the app lists the Section 8 clause cited, what it normally covers, and the usual grounds for appeal. Must stay explanatory, not legal advice.
3. **Pre-payment checklist and attachment checker** (the seven failure reasons; file name, no Aadhaar or PAN).
4. **Deadline reminders** by email or WhatsApp with the appeal windows already computed.
5. **Assisted and low-bandwidth mode** for rural users (voice first, operator-assisted filing).
6. **Grouped multi-CPIO view and "documents required" inbox.**

## 5. What not to claim in a pitch

- That the app files real RTIs, or that payment is real.
- That all 22 languages work. Hindi and English are tested; others are beta.
- That any 2026 figure above is exact. Quote the source and date.
- That the second-appeal opportunity is proven: returns are documented, but whether a checker would prevent them is a hypothesis.

## Sources

- rtionline.gov.in: Guidelines (request and appeal) and FAQ, read 30 Oct 2026
- [ThePrint/PTI, "RTI at 21: 3.85 lakh cases pending, procedural hurdles flagged in returned appeals"](https://theprint.in/india/rti-at-21-3-85-lakh-cases-pending-procedural-hurdles-flagged-in-returned-appeals/3070554/)
- [Satark Nagrik Sangathan 2025 press release](https://www.snsindia.org/wp-content/uploads/2025/10/Press-Release-2025.pdf)
- [The Wire, information commissions' performance 2024-25](https://m.thewire.in/article/rights/short-staffed-defunct-and-headless-how-information-commissions-performed-in-2024-25)
- [Moneylife, "1 out of every 3 RTIs is rejected using Section 8(1)", CIC annual report 2019-20](https://moneylife.in/article/1-out-of-every-3-rtis-is-rejected-using-section-8-1-says-cic-annual-report-201920/63685.html)
- [Moneylife, rejection of information under RTI](https://www.moneylife.in/article/rejection-of-information-under-rti-quite-common-except-in-information-commission-reports/34998.html)
- [Bar and Bench on DPDP Section 44(3)](https://www.barandbench.com/columns/section-443-of-the-dpdp-act-cloaking-indias-right-to-know-in-secrecy)
- [Moneylife, Supreme Court notice on DPDP and RTI](https://moneylife.in/article/supreme-court-issues-notice-on-pleas-challenging-dpdp-acts-impact-on-rti-act/80577.html)
- [The Week, RTI Act at 20 and activist protection](https://www.theweek.in/theweek/cover/2025/10/04/rti-act-at-20-why-india-needs-better-whistleblower-protection-for-activists.html)
- [Wikipedia, attacks on RTI activists in India](https://en.wikipedia.org/wiki/Attacks_on_RTI_activists_in_India) (CHRI figure is cited there)
