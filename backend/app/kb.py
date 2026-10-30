"""Small RTI knowledge base for the help assistant.

Portal facts (ids: which, limit, payment, appeal1, firstappeal_portal, state_portal, fee, bpl) come from
rtionline.gov.in "Guidelines" and "FAQ" pages as read on 2026-10-30. Act facts come from the RTI Act, 2005
as the author understands them. State rules differ. This is NOT legal advice; verify before relying on it.
"""

PASSAGES = [
    {"id": "who", "title": "Who can apply",
     "text": "Any citizen of India can ask for information from a public authority under Section 3 of the RTI Act, 2005. You do not have to give a reason for wanting the information."},
    {"id": "how", "title": "How to apply",
     "text": "Send a written or electronic request to the Public Information Officer (PIO) of the authority concerned, as set out in Section 6(1). Ask clear, specific questions about one subject. The Act covers information held as records, documents, files, reports and similar; a PIO is not required to create new information, give opinions, or answer hypothetical questions."},
    {"id": "fee", "title": "Fee",
     "text": "The fee for an application is as prescribed in the RTI Rules, 2012; for central public authorities it is Rs 10, and copies cost Rs 2 per A4 page. If extra fee is needed for the cost of providing information, the CPIO tells you through the portal Status page and by email or SMS. States set their own fee, so check the state's rules. Payment on the portal is by internet banking, Mastercard or Visa cards, RuPay cards or UPI."},
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
     "text": "The online portal rtionline.gov.in is only for Ministries, Departments and other public authorities of the Central Government listed in its form. State public authorities, such as state police, electricity boards, municipal bodies and land records, are not on it. If you file a state matter there, the application is returned without any refund of the fee. If you pick the wrong central authority, the Nodal Officer transfers it to the right one under Section 6(3)."},
    {"id": "limit", "title": "Online text limit and allowed characters",
     "text": "The request text on the portal is limited to 3000 characters. Only English letters A-Z a-z, digits 0-9 and the characters , . - _ ( ) / @ : & ? \\ % are allowed in it. If your text is longer, or not in English, upload it as a PDF in Supporting document. The PDF file name must not contain spaces. Do not upload Aadhaar or PAN cards; only a BPL certificate is accepted as an identity-type document."},
    {"id": "payment", "title": "If money is cut but there is no registration number",
     "text": "Do not pay again and do not submit the request a second time. The registration number is generated after reconciliation, which can take 24 to 48 working hours. You can use the Payment Reconciliation option on the portal to check earlier. If there is still no number after 24 to 48 working hours, email helprtionline-dopt[at]nic[dot]in with your transaction details, or ask your bank for a refund. In this redesign the request shows Confirming instead of Failed and the app keeps checking."},
    {"id": "paymentfail", "title": "Why an online payment fails",
     "text": "The portal lists these common reasons: the card has e-commerce use disabled; the browser was closed or the session timed out; a wrong or missing OTP; wrong card number, CVV or expiry; insufficient balance; the person cancelled and tried another payment mode; or a UPI collect request was not approved in time."},
    {"id": "firstappeal_portal", "title": "First appeal on the portal",
     "text": "No fee is charged for a first appeal. To file it online you need the registration number and email ID of the original online application. Online first appeal works only for applications that were filed online. The portal will not let you file if the application was physically transferred to an authority not on the portal (file on paper to that authority), or if the CPIO has not replied and the 30 days have not yet passed."},
    {"id": "bpl", "title": "Fee exemption",
     "text": "No fee is required from a citizen below the poverty line under the RTI Rules, 2012, but a copy of the certificate issued by the appropriate government must be attached with the application."},
    {"id": "tips", "title": "Writing a good request",
     "text": "Name the department, the place and the period you mean. Ask for records such as file notings, copies of orders, tender documents or bills instead of asking why something happened. Number your questions. Keep a copy of what you sent and note the date."},
]
