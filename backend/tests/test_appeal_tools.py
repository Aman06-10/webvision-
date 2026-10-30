from datetime import date, timedelta

from app import appeal_docs, attachments, drafts, reminders, reply_review

T = date(2026, 10, 30)
D = lambda n: (T - timedelta(days=n)).isoformat()


def codes(res, level=None):
    return {i["code"] for i in res["issues"] if level is None or i["level"] == level}


def good_second(**over):
    d = dict(name="A Citizen", address="12 Road, Jaipur", authority="Ministry X", cpio_to="CPIO, Ministry X",
             faa="FAA, Ministry X", filed_on=D(120), first_appeal_on=D(70), fa_order_on=D(30), fa_order_no="12/2026",
             reg_no="MINX/R/2026/1", sought="File notings", facts="I filed on the date and got a partial reply.",
             prayer="Direct the CPIO to give the complete information.",
             grounds="The information is incomplete and the reasons given do not support the exemption cited.",
             docs=dict(doc_application=True, doc_first_appeal=True, doc_reply=True, doc_fa_order=True),
             signed=True, verified_docs=True, legible=True, related=True, index=True, service_proof=True,
             phone="9999999999", email="a@b.c")
    d.update(over)
    return d


def test_complete_second_appeal_is_ready():
    r = appeal_docs.second_appeal(good_second(), T)
    assert r["ready"], r["issues"]
    assert "11. Verification" in r["text"] and "Index of documents" in r["text"]
    assert "Rule 8" not in r["text"] and r["text"].count("\n10. ") == 1


def test_missing_mandatory_items_are_errors():
    d = good_second(docs=dict(doc_reply=True), signed=False, index=False, service_proof=False)
    r = appeal_docs.second_appeal(d, T)
    assert not r["ready"]
    assert {"no_doc_application", "no_doc_first_appeal", "unsigned", "no_index", "no_service_proof"} <= codes(r, "error")


def test_no_first_appeal_is_flagged_as_returnable():
    r = appeal_docs.second_appeal(good_second(first_appeal_on="", fa_order_on=""), T)
    assert "no_first_appeal" in codes(r, "error") and not r["ready"]


def test_too_early_before_45_days_without_order():
    r = appeal_docs.second_appeal(good_second(first_appeal_on=D(20), fa_order_on=""), T)
    assert "too_early" in codes(r, "error")
    assert appeal_docs.second_appeal(good_second(first_appeal_on=D(50), fa_order_on=""), T)["ready"]


def test_late_needs_condonation_request():
    late = good_second(fa_order_on=D(120), first_appeal_on=D(150), filed_on=D(200))
    r = appeal_docs.second_appeal(late, T)
    assert "needs_condonation" in codes(r, "error")
    r = appeal_docs.second_appeal({**late, "condonation": "I was hospitalised for two months."}, T)
    assert r["ready"] and "late_with_condonation" in codes(r, "warning") and "condonation of delay" in r["text"]


def test_compensation_needs_grounds():
    r = appeal_docs.second_appeal(good_second(compensation=True), T)
    assert "compensation_grounds" in codes(r, "warning")


def test_first_appeal_draft_and_timing():
    d = dict(name="A", address="B", authority="Ministry X", filed_on=D(40), grounds=["no_reply"], reg_no="R1", sought="records")
    r = appeal_docs.first_appeal(d, T)
    assert r["ready"] and "Section 7(1)" in r["text"] and "R1" in r["text"]
    r = appeal_docs.first_appeal({**d, "filed_on": D(10)}, T)
    assert not r["ready"] and "too_early" in codes(r, "error")
    r = appeal_docs.first_appeal({**d, "filed_on": D(120)}, T)
    assert r["ready"] and "late" in codes(r, "warning")
    assert "missing_grounds" in codes(appeal_docs.first_appeal({**d, "grounds": []}, T), "error")


def test_reply_review_finds_clauses_and_gaps():
    r = reply_review.review("The information is denied under Section 8(1)(j) of the RTI Act.")
    assert [c["ref"] for c in r["clauses"]] == ["8(1)(j)"]
    assert "no_appeal_info" in {f["code"] for f in r["flags"]} and "public_interest" in r["suggested_grounds"]


def test_reply_review_refusal_without_clause():
    r = reply_review.review("Your request is rejected as it cannot be provided.")
    assert {f["code"] for f in r["flags"]} >= {"no_clause", "no_appeal_info"}
    assert "wrong_exemption" in r["suggested_grounds"]


def test_reply_review_other_sections_and_phrases():
    r = reply_review.review("As per Section 11 the third party objected; records are not available. Appeal lies to the FAA.")
    assert [o["ref"] for o in r["other_sections"]] == ["11"]
    assert {"not_available", "third_party"} <= {f["code"] for f in r["flags"]}


def test_attachment_rules():
    assert not attachments.check("my id aadhaar.pdf")["ok"]
    r = attachments.check("scan 1.pdf")
    assert not r["ok"] and any("scan_1.pdf" in i["message"] for i in r["issues"])
    assert attachments.check("bpl certificate.pdf", kind="bpl")["issues"][0]["code"] == "spaces"
    assert attachments.check("bpl_aadhaar_card.pdf", kind="bpl")["ok"]
    assert attachments.check("details.pdf")["ok"]
    assert any(i["code"] == "not_pdf" for i in attachments.check("details.docx")["issues"])


def test_reminders_dates_and_states():
    items = reminders.for_request(date(2026, 1, 1), date(2026, 1, 28))
    assert [i["kind"] for i in items] == ["reply_soon", "appeal_opens", "appeal_closing"]
    assert items[0]["date"] == "2026-01-26" and items[0]["state"] == "past"
    assert items[1]["date"] == "2026-02-01" and items[1]["state"] == "upcoming" and items[1]["days"] == 4
    assert reminders.for_request(date(2026, 1, 1), date(2026, 2, 1))[1]["state"] == "due"


def test_request_hints():
    h = {x["code"] for x in drafts.analyze_request("Why was it delayed? Give your opinion.")}
    assert {"question_style", "no_record"} <= h
    assert "id_number" in {x["code"] for x in drafts.analyze_request("Copy of file for Aadhaar 1234 5678 9012")}
    assert "id_number" in {x["code"] for x in drafts.analyze_request("PAN ABCDE1234F copy of order")}
    assert drafts.analyze_request("Please provide a copy of the file notings on the tender dated 3 March.") == []
