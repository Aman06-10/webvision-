"""Small RTI knowledge base for the help assistant.

General guidance drawn from the RTI Act, 2005 and the central RTI Rules, 2012 as the
author understands them. State rules differ. This is NOT legal advice; verify against
the Act or the authority's own page before relying on a figure.
"""

PASSAGES = [
    {"id": "who", "title": "Who can apply",
     "text": "Any citizen of India can ask for information from a public authority under Section 3 of the RTI Act, 2005. You do not have to give a reason for wanting the information."},
    {"id": "how", "title": "How to apply",
     "text": "Send a written or electronic request to the Public Information Officer (PIO) of the authority concerned, as set out in Section 6(1). Ask clear, specific questions about one subject. The Act covers information held as records, documents, files, reports and similar; a PIO is not required to create new information, give opinions, or answer hypothetical questions."},
    {"id": "fee", "title": "Fee",
     "text": "Under the central RTI Rules, 2012 the application fee for a central public authority is Rs 10. Copies cost Rs 2 per A4 page. Applicants below the poverty line are exempt from the fee when they attach proof. States set their own fee, so check the state's rules."},
    {"id": "time", "title": "Time to reply",
     "text": "The PIO must reply within 30 days of receiving the request (Section 7(1)). If the information concerns a person's life or liberty, the reply is due within 48 hours. If the request goes through an Assistant PIO, add 5 days. If the request belongs to another authority, it must be transferred within 5 days (Section 6(3))."},
    {"id": "appeal1", "title": "First appeal",
     "text": "If you get no reply or are unhappy with it, file a first appeal with the First Appellate Authority of the same office within 30 days (Section 19(1)). That authority should decide within 30 days, extendable to 45 days in total."},
    {"id": "appeal2", "title": "Second appeal",
     "text": "If the first appeal does not solve the matter, you can file a second appeal with the Central or State Information Commission within 90 days of the first appeal decision, or of the date it was due (Section 19(3))."},
    {"id": "exempt", "title": "What can be refused",
     "text": "Section 8 lists information that can be withheld, such as matters affecting the sovereignty and security of the country, information barred by a court, cabinet papers before a decision, trade secrets, and personal information with no public interest. Section 8(2) allows disclosure where the public interest outweighs the harm. Certain security and intelligence bodies are exempt under Section 24."},
    {"id": "penalty", "title": "Penalty for delay",
     "text": "Under Section 20, an Information Commission can penalise a PIO Rs 250 for each day of delay, up to Rs 25,000, if the PIO refused or delayed without reasonable cause, or gave wrong or misleading information."},
    {"id": "which", "title": "Which authority or portal",
     "text": "Requests to central government ministries and departments can go through the central online portal, rtionline.gov.in. State government bodies such as state police, electricity boards, municipal bodies and land records follow their own state's RTI process. File with the authority that actually holds the records; a request to the wrong authority is usually transferred, which costs time, or rejected."},
    {"id": "limit", "title": "Online text limit",
     "text": "The online application form allows about 3000 characters for the request text, and accepts only a limited set of characters. Keep requests short and numbered; attach documents separately if needed."},
    {"id": "payment", "title": "Payment problems in this app",
     "text": "In this redesign, if the bank does not confirm your payment straight away, the request shows 'Confirming' instead of 'Failed'. Do not pay again. The app checks with the bank on its own, and your RTI number appears once payment is confirmed. A second payment for the same request is blocked."},
    {"id": "tips", "title": "Writing a good request",
     "text": "Name the department, the place and the period you mean. Ask for records such as file notings, copies of orders, tender documents or bills instead of asking why something happened. Number your questions. Keep a copy of what you sent and note the date."},
]
