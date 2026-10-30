"""Check an attachment's name against the RTI Online guidelines (no file contents are read or stored).

Guidelines (rtionline.gov.in, read 2026-10-30): supporting documents go in as PDF; the PDF file name must have
no blank spaces; do not upload Aadhaar, PAN or other identity documents except a BPL certificate.
The guidelines read do not state a file-size limit, so none is enforced here.
"""
import re

ID_WORDS = re.compile(r"aadhaar|aadhar|uidai|\bpan\b|pan[_ -]?card|voter|passport|driving|licen[cs]e|ration", re.I)


def check(filename: str, size_bytes: int | None = None, kind: str = "supporting") -> dict:
    issues = []
    name = filename or ""
    if " " in name:
        issues.append({"code": "spaces", "level": "error", "message": "The file name has spaces. Rename it with underscores, for example " + name.replace(" ", "_") + "."})
    if not name.lower().endswith(".pdf"):
        issues.append({"code": "not_pdf", "level": "warning", "message": "The guidelines describe supporting documents as PDFs. Convert it to PDF unless the form says otherwise."})
    if ID_WORDS.search(name) and kind != "bpl":
        issues.append({"code": "id_document", "level": "error", "message": "The name suggests an identity document. The portal says not to upload Aadhaar, PAN or similar. Only a BPL certificate is expected."})
    if size_bytes is not None and size_bytes == 0:
        issues.append({"code": "empty", "level": "error", "message": "The file is empty."})
    if not issues:
        issues.append({"code": "ok", "level": "ok", "message": "The name follows the guidelines. Check that the pages are legible before uploading."})
    return {"ok": not any(i["level"] == "error" for i in issues), "issues": issues}
