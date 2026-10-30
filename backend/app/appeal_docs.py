"""Draft and check first and second appeals.

Second appeal format and checklist come from the CIC's own pages on cic.gov.in (Second Appeal Guidelines
and FAQ, read 2026-10-30), which cite Rules 8 and 9 of the RTI Rules, 2012:
- Format of appeal (Rule 8): 1 appellant name and address; 2 CPIO the application went to; 3 CPIO who replied;
  4 First Appellate Authority; 5 particulars of the application; 6 particulars of the order(s) appealed;
  7 brief facts; 8 prayer or relief; 9 grounds; 10 any other relevant information; 11 verification.
- Mandatory: signed appeal addressed to the Commission, copy of the RTI application, copy of the first appeal;
  all related to each other; legible; Hindi or English (or translated).
- If available: CPIO reply, first appellate order, other relied documents, and an index. All documents signed,
  self-attested or verified by the appellant. One copy, with proof of service on the CPIO and the FAA.
- A second appeal without a first appeal is liable to be returned. A late appeal needs a formal request for
  condonation of delay or it is liable to be rejected.
Page numbering is not in those pages (only recommended by third parties), so it is a suggestion here.
The checker lists what to fix. It cannot promise the Commission will accept an appeal. Not legal advice.
"""
from datetime import date

from . import appeal

# Standard grounds a first appeal can rest on. Keys are shared with reply_review suggestions.
GROUNDS = {
    "no_reply": "No reply was received within the 30 days allowed under Section 7(1) of the RTI Act, 2005.",
    "incomplete": "The information given is incomplete. The items listed below were not provided.",
    "wrong_exemption": "The exemption cited does not apply to the information sought, and the reasons given do not show how disclosure would cause the harm the clause protects against.",
    "no_reasons": "The rejection does not state the reasons for rejection, the period for appeal and the particulars of the appellate authority, as Section 7(8) requires.",
    "partial_denial": "Part of the information could have been disclosed with the exempt portion severed, as Section 10 provides, but the whole request was refused.",
    "misleading": "The information supplied is misleading or does not correspond to what was asked.",
    "fee_unreasonable": "The additional fee demanded is not justified by the cost of providing the information.",
    "transfer_delay": "The application was not transferred to the correct authority within the 5 days allowed by Section 6(3), or was transferred without reason.",
    "public_interest": "Even if an exemption applies, the larger public interest in disclosure outweighs the harm, as Section 8(2) allows.",
}
RELIEF = {
    "provide": "Direct the CPIO to provide the information sought, free of charge where the reply was late.",
    "complete": "Direct the CPIO to provide the complete information listed above.",
    "inspect": "Allow inspection of the relevant records and certified copies of the portions I select.",
    "reconsider": "Set aside the rejection and decide the request afresh with reasons.",
}


def _issue(code: str, level: str, text: str) -> dict:
    return {"code": code, "level": level, "message": text}


def _blank(v) -> bool:
    return v is None or not str(v).strip()


# ---- first appeal ------------------------------------------------------
def first_appeal(d: dict, today: date | None = None) -> dict:
    today = today or date.today()
    issues = []
    for k, label in (("name", "your name"), ("address", "your address"), ("authority", "the public authority"),
                     ("filed_on", "the date you filed the RTI request")):
        if _blank(d.get(k)):
            issues.append(_issue(f"missing_{k}", "error", f"Add {label}."))
    grounds = [g for g in d.get("grounds", []) if g in GROUNDS]
    if not grounds and _blank(d.get("extra")):
        issues.append(_issue("missing_grounds", "error", "Pick at least one ground or write your own."))
    filed = d.get("filed_on")
    status = None
    if filed:
        try:
            replied = d.get("replied_on") or None
            status = appeal.assess(date.fromisoformat(filed), today,
                                   date.fromisoformat(replied) if replied else None)
        except ValueError as e:
            issues.append(_issue("bad_dates", "error", str(e)))
    if status and not status["can_first_appeal"]:
        if status["stage"] == "waiting_reply":
            issues.append(_issue("too_early", "error", f"The 30 days for a reply end on {status['dates']['reply_due']}. "
                                 "Without a reply you can appeal from the next day."))
        elif status["stage"] == "first_appeal_closed":
            issues.append(_issue("late", "warning", "The usual 30-day window has passed. Add a short request to admit "
                                 "the appeal late and explain the delay."))
    if _blank(d.get("reg_no")):
        issues.append(_issue("no_regno", "warning", "Add the registration number if you filed online; the portal needs it with your email."))
    if d.get("reply_summary") and d.get("replied_on") is None:
        issues.append(_issue("reply_date", "warning", "You described a reply but gave no reply date."))

    lines = [
        "To,", "The First Appellate Authority,", d.get("authority") or "[Public authority]", "",
        "Subject: First appeal under Section 19(1) of the Right to Information Act, 2005", "",
        f"Appellant: {d.get('name') or '[Name]'}", f"Address: {d.get('address') or '[Address]'}",
    ]
    if d.get("phone") or d.get("email"):
        lines.append(f"Contact: {', '.join(x for x in (d.get('phone'), d.get('email')) if x)}")
    lines += ["", f"RTI registration number: {d.get('reg_no') or '[Registration number]'}",
              f"Date of RTI application: {d.get('filed_on') or '[Date]'}",
              f"CPIO: {d.get('cpio') or '[CPIO, if known]'}"]
    if d.get("replied_on"):
        lines.append(f"Date of reply: {d['replied_on']}")
    if d.get("reply_summary"):
        lines += ["", "Reply received (summary):", d["reply_summary"]]
    lines += ["", "Information sought:", d.get("sought") or "[What you asked for, as in your original request]", "",
              "Grounds for appeal:"]
    for i, g in enumerate(grounds, 1):
        lines.append(f"{i}. {GROUNDS[g]}")
    if not _blank(d.get("extra")):
        lines.append(f"{len(grounds) + 1}. {d['extra'].strip()}")
    rel = RELIEF.get(d.get("relief"), RELIEF["provide"])
    lines += ["", "Relief sought:", rel, "",
              "I request that this appeal be decided within the time allowed by Section 19(6) of the Act.", "",
              f"Date: {today.isoformat()}", "Place: ________", "", "Signature: ________________"]
    ready = not any(i["level"] == "error" for i in issues)
    return {"ready": ready, "issues": issues, "text": "\n".join(lines), "assessment": status}


# ---- second appeal -----------------------------------------------------
DOCS = [
    ("doc_application", "Copy of the RTI application sent to the CPIO", True),
    ("doc_first_appeal", "Copy of the first appeal sent to the First Appellate Authority", True),
    ("doc_reply", "Copy of the CPIO's reply, if any", False),
    ("doc_fa_order", "Copy of the First Appellate Authority's order, if any", False),
    ("doc_other", "Other documents you rely on and refer to in the appeal", False),
]


def second_appeal(d: dict, today: date | None = None) -> dict:
    today = today or date.today()
    issues = []
    docs = d.get("docs", {})

    for k, label in (("name", "your name"), ("address", "your address"), ("authority", "the public authority"),
                     ("cpio_to", "the CPIO the application was addressed to"),
                     ("faa", "the First Appellate Authority who decided or should have decided"),
                     ("filed_on", "the date of the RTI application"),
                     ("first_appeal_on", "the date of the first appeal"),
                     ("facts", "a brief statement of facts"), ("grounds", "your grounds"),
                     ("prayer", "your prayer: what you want the Commission to order")):
        if _blank(d.get(k)):
            issues.append(_issue(f"missing_{k}", "error", f"Add {label}."))

    for code, label, mandatory in DOCS:
        if mandatory and not docs.get(code):
            issues.append(_issue(f"no_{code}", "error", f"Attach: {label}. The Commission lists it as mandatory."))
    if not d.get("signed"):
        issues.append(_issue("unsigned", "error", "Sign the appeal. It must be signed and addressed to the Commission."))
    if not d.get("verified_docs"):
        issues.append(_issue("unverified_docs", "error", "Sign or self-attest every attached document before scanning."))
    if not d.get("legible"):
        issues.append(_issue("not_legible", "error", "Make sure every document is legible and in Hindi or English, or add a translation."))
    if not d.get("related"):
        issues.append(_issue("not_related", "error", "The RTI application, first appeal and second appeal must relate to the same matter."))
    if not d.get("index"):
        issues.append(_issue("no_index", "error", "Add an index of the documents referred to in the appeal."))
    if not d.get("service_proof"):
        issues.append(_issue("no_service_proof", "error", "Attach proof that you sent a copy of the appeal to the CPIO and the First Appellate Authority."))

    status = None
    try:
        filed = date.fromisoformat(d["filed_on"]) if d.get("filed_on") else None
        fa = date.fromisoformat(d["first_appeal_on"]) if d.get("first_appeal_on") else None
        dec = date.fromisoformat(d["fa_order_on"]) if d.get("fa_order_on") else None
        if filed and fa:
            status = appeal.assess(filed, today, first_appeal=fa, fa_decided=dec)
    except ValueError as e:
        issues.append(_issue("bad_dates", "error", str(e)))
    if not d.get("first_appeal_on"):
        issues.append(_issue("no_first_appeal", "error", "A second appeal filed without a first appeal is liable to be returned. File the first appeal first."))
    if status:
        if status["stage"] == "first_appeal_pending":
            issues.append(_issue("too_early", "error", f"The Commission accepts a second appeal without an order only after 45 days from the first appeal, so from {status['dates']['second_appeal_opens']}."))
        elif status["stage"] == "second_appeal_closed":
            if _blank(d.get("condonation")):
                issues.append(_issue("needs_condonation", "error", f"The 90 days ended on {status['dates']['second_appeal_deadline']}. Add a formal request for condonation of delay with the reason, or the appeal is liable to be rejected."))
            else:
                issues.append(_issue("late_with_condonation", "warning", "You are late, so the Commission will decide whether your reason is sufficient cause."))

    if d.get("compensation") and _blank(d.get("compensation_grounds")):
        issues.append(_issue("compensation_grounds", "warning", "If you ask for compensation, give specific grounds and describe the detriment you suffered."))
    if not d.get("similar_order"):
        issues.append(_issue("similar_order", "info", "If the Commission has already ordered this authority on a similar issue, attach that order. It can speed up disposal."))
    if _blank(d.get("phone")) or _blank(d.get("email")):
        issues.append(_issue("contact", "warning", "Give a mobile number and email so the Commission can reach you."))
    if not _blank(d.get("grounds")) and not _blank(d.get("prayer")) and len(str(d["grounds"]).strip()) < 40:
        issues.append(_issue("thin_grounds", "info", "Grounds are very short. Say what was asked, what was not given, and why you are unhappy."))

    idx = [(label, c) for c, label, _ in DOCS if docs.get(c)]
    lines = [
        "To,", "The Central Information Commission,", "Baba Gang Nath Marg, Munirka, New Delhi 110067", "",
        "Second appeal under Section 19(3) of the Right to Information Act, 2005", "",
        f"1. Name and address of the appellant: {d.get('name') or '[Name]'}, {d.get('address') or '[Address]'}",
        f"2. Name and address of the CPIO to whom the application was addressed: {d.get('cpio_to') or '[CPIO]'}",
        f"3. Name and address of the CPIO who gave the reply: {d.get('cpio_reply') or 'No reply received' if _blank(d.get('cpio_reply')) else d['cpio_reply']}",
        f"4. Name and address of the First Appellate Authority who decided the first appeal: {d.get('faa') or '[FAA]'}",
        f"5. Particulars of the application: dated {d.get('filed_on') or '[date]'}, registration number {d.get('reg_no') or '[number, if any]'}. "
        f"Information sought: {d.get('sought') or '[summary]'}",
        f"6. Particulars of the order against which the appeal is made: " +
        (f"First Appellate Authority order dated {d['fa_order_on']}" + (f", number {d['fa_order_no']}" if d.get('fa_order_no') else "")
         if d.get("fa_order_on") else f"No order was passed on the first appeal filed on {d.get('first_appeal_on') or '[date]'}."),
        "7. Brief facts leading to the appeal:", d.get("facts") or "[Facts]",
        "8. Prayer or relief sought:", d.get("prayer") or "[Prayer]",
        "9. Grounds for the prayer or relief:", d.get("grounds") or "[Grounds]",
        "10. Any other information relevant to the appeal:", d.get("other") or "None.",
    ]
    if d.get("compensation"):
        lines += ["Compensation: " + (d.get("compensation_grounds") or "[Grounds and details of loss or detriment]")]
    if not _blank(d.get("condonation")):
        lines += ["", "Request for condonation of delay:", d["condonation"].strip()]
    lines += ["", "11. Verification: I verify that the contents of this appeal are true to the best of my knowledge "
              "and belief, and that the documents enclosed are true copies, signed by me.", "",
              f"Date: {today.isoformat()}", "Place: ________", "Signature of appellant: ________________", "",
              "Contact: " + ", ".join(x for x in (d.get("phone"), d.get("email")) if x), "",
              "Index of documents (number every page consecutively and fill in the page numbers):",
              "No.  Document  Pages"]
    for n, (label, _) in enumerate(idx, 1):
        lines.append(f"{n}.  {label}  ____")
    lines.append(f"{len(idx) + 1}.  Proof of service of this appeal on the CPIO and the First Appellate Authority  ____")
    ready = not any(i["level"] == "error" for i in issues)
    return {"ready": ready, "issues": issues, "text": "\n".join(lines), "assessment": status}
