"""Explain a CPIO's reply: which exemption it cites, what that clause covers, and common grounds to challenge.

Section summaries paraphrase the RTI Act, 2005 as the author understands it. This explains; it does not
judge whether a particular refusal is lawful. Not legal advice. Clause (j) is under legal challenge after
the DPDP Act, 2023 amendment; check the current text.
"""
import re

SECTION_8 = {
    "a": ("Security and foreign relations", "Information that would harm India's sovereignty, security, strategic, scientific or economic interests, relations with a foreign state, or lead to incitement of an offence.", ["wrong_exemption", "partial_denial"]),
    "b": ("Barred by a court", "Information a court or tribunal has expressly forbidden to be published, or whose disclosure would be contempt of court.", ["wrong_exemption"]),
    "c": ("Privilege of the legislature", "Information whose disclosure would breach the privilege of Parliament or a State Legislature.", ["wrong_exemption"]),
    "d": ("Commercial confidence", "Commercial confidence, trade secrets or intellectual property that would harm a third party's competitive position, unless the larger public interest justifies disclosure.", ["wrong_exemption", "public_interest", "partial_denial"]),
    "e": ("Fiduciary relationship", "Information held in a fiduciary relationship, unless the larger public interest justifies disclosure.", ["wrong_exemption", "public_interest"]),
    "f": ("Confidence of a foreign government", "Information received in confidence from a foreign government.", ["wrong_exemption"]),
    "g": ("Safety and sources", "Information that would endanger a person's life or physical safety, or identify a confidential source for law enforcement or security.", ["wrong_exemption", "partial_denial"]),
    "h": ("Investigation", "Information that would impede an investigation, or the apprehension or prosecution of offenders.", ["wrong_exemption", "no_reasons"]),
    "i": ("Cabinet papers", "Cabinet papers and deliberations. The decisions, reasons and material are to be made public after the decision is taken and the matter is complete.", ["wrong_exemption"]),
    "j": ("Personal information", "Personal information with no relationship to any public activity or interest, or whose disclosure would be an unwarranted invasion of privacy, unless the larger public interest justifies it. Information that cannot be denied to Parliament cannot be denied to anyone. This clause is the most often cited and is contested after the DPDP Act amendment.", ["wrong_exemption", "public_interest", "partial_denial"]),
}
OTHER_SECTIONS = {
    "8(2)": ("Public interest override", "An authority may allow access even to exempt information if the public interest in disclosure outweighs the harm."),
    "8(3)": ("Old records", "Information about events more than 20 years old is generally to be provided, with some exceptions."),
    "9": ("Copyright", "A request can be refused if giving access would infringe a private person's copyright."),
    "10": ("Severability", "If only part of a record is exempt, the rest must be given after severing the exempt portion."),
    "11": ("Third party information", "Before disclosing information a third party treated as confidential, the CPIO must notify that party and consider its objection."),
    "7(9)": ("Form of information", "Information is ordinarily given in the form asked for unless that would disproportionately divert the authority's resources or harm the record."),
    "24": ("Exempt organisations", "Listed security and intelligence organisations are exempt, except on corruption and human rights violations."),
}

PHRASES = [
    (r"not (available|traceable)|does not exist|not (held|maintained)", "not_available",
     "The reply says the information is not available. You can ask for an inspection of the file, a certified statement of what was searched, and who is responsible for the record."),
    (r"not (come|fall)s? under (the )?definition of information|not information|query|clarification|opinion|why\b", "not_information",
     "The reply treats the request as a question or opinion. Rewrite what you want as copies of records, such as orders, file notings or reports."),
    (r"vague|unclear|not specific|not clear", "vague",
     "The reply calls the request vague. A PIO is expected to help an applicant who needs it (Section 5(3)). Appeal with a clear list of the records you want."),
    (r"voluminous|disproportionate|divert", "voluminous",
     "The reply says the request is too large. Section 7(9) allows a refusal only for disproportionate diversion of resources. You can narrow the period or ask for inspection."),
    (r"third party|confidential", "third_party",
     "The reply points to a third party. The CPIO must follow Section 11 before refusing. Ask whether the third party was notified."),
    (r"transferred|forwarded", "transferred",
     "The request was transferred. Section 6(3) needs this within 5 days; note the date and the new authority."),
]

CLAUSE_RE = re.compile(r"8\s*\(\s*1\s*\)\s*\(\s*([a-j])\s*\)", re.I)
SECTION_RE = re.compile(r"(?:section|sec\.?|s\.)\s*(8\s*\(\s*2\s*\)|8\s*\(\s*3\s*\)|7\s*\(\s*9\s*\)|24|11|10|9)\b", re.I)


def review(text: str) -> dict:
    t = text or ""
    clauses = []
    for letter in dict.fromkeys(m.group(1).lower() for m in CLAUSE_RE.finditer(t)):
        title, summary, grounds = SECTION_8[letter]
        clauses.append({"ref": f"8(1)({letter})", "title": title, "summary": summary, "grounds": grounds})
    others = []
    for m in SECTION_RE.finditer(t):
        ref = re.sub(r"\s+", "", m.group(1))
        if ref in OTHER_SECTIONS and ref not in [o["ref"] for o in others]:
            title, summary = OTHER_SECTIONS[ref]
            others.append({"ref": ref, "title": title, "summary": summary})
    flags, grounds = [], []
    low = t.lower()
    for pat, code, msg in PHRASES:
        if re.search(pat, low):
            flags.append({"code": code, "message": msg})
    refusing = bool(re.search(r"reject|denied|refus|cannot be (provided|furnished|given)|exempt", low))
    if refusing and not clauses and not others:
        flags.append({"code": "no_clause", "message": "The reply refuses or withholds information but does not name any section of the Act. A refusal has to rest on a specific exemption."})
        grounds.append("wrong_exemption")
    if refusing and not re.search(r"appeal|appellate", low):
        flags.append({"code": "no_appeal_info", "message": "A rejection should say why, within what time you can appeal, and to which authority (Section 7(8)). This reply mentions none of that."})
        grounds.append("no_reasons")
    for c in clauses:
        grounds += c["grounds"]
    if any(f["code"] == "not_information" for f in flags):
        grounds.append("incomplete")
    if any(c["ref"] == "8(1)(j)" for c in clauses):
        flags.append({"code": "j_caveat", "message": "Clause (j) is the most cited exemption. Ask what the personal information is, how it relates to no public activity, and whether the public interest was weighed."})
    return {"clauses": clauses, "other_sections": others, "flags": flags,
            "suggested_grounds": list(dict.fromkeys(grounds)),
            "empty": not t.strip()}
