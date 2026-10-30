"""Appeal eligibility: why the appeal option is open or closed, and the dates that matter.

Rules used (RTI Act, 2005, as the author understands it, plus the rtionline.gov.in FAQ):
- The authority should reply within 30 days of the application (Section 7(1)).
- First appeal (Section 19(1)): within 30 days of the reply, or of the day the 30-day reply period
  ended if there was no reply. No fee. On the portal it stays closed until the 30 days have passed
  if there is no reply, and for applications physically transferred to an authority not on the portal.
- The first appeal should be decided within 30 days (up to 45 with reasons) (Section 19(6)).
- Second appeal to the Information Commission within 90 days of the first appeal decision, or of
  the date it should have been decided (Section 19(3)).
Late appeals can be admitted for "sufficient cause", which this module does not judge.
We count the earliest reasonable dates, so a result never promises more time than the user has.
Not legal advice.
"""
from datetime import date, timedelta

REPLY_DAYS = 30
FIRST_APPEAL_DAYS = 30
FA_DECISION_DAYS = 30
FA_DECISION_MAX_DAYS = 45
SECOND_APPEAL_DAYS = 90


def _d(d: date, n: int) -> date:
    return d + timedelta(days=n)


def assess(filed: date, today: date, replied: date | None = None, first_appeal: date | None = None,
           fa_decided: date | None = None, transferred_physically: bool = False) -> dict:
    """Returns {stage, can_first_appeal, can_second_appeal, reason, dates, days_left}.
    Dates are ISO strings; days_left is signed (negative = already past)."""
    if filed > today:
        raise ValueError("filed date is in the future")
    for name, v in (("replied", replied), ("first_appeal", first_appeal), ("fa_decided", fa_decided)):
        if v and v < filed:
            raise ValueError(f"{name} date is before the filing date")
        if v and v > today:
            raise ValueError(f"{name} date is in the future")
    if first_appeal and replied and first_appeal < replied:
        pass  # allowed: appeal filed before a late reply arrived

    reply_due = _d(filed, REPLY_DAYS)
    dates = {"reply_due": reply_due}
    # first-appeal window
    if replied:
        fa_open, fa_close = replied, _d(replied, FIRST_APPEAL_DAYS)
    else:
        fa_open, fa_close = _d(reply_due, 1), _d(reply_due, FIRST_APPEAL_DAYS)
    dates.update(first_appeal_opens=fa_open, first_appeal_deadline=fa_close)

    out = {"can_first_appeal": False, "can_second_appeal": False, "reason": "", "stage": ""}

    if first_appeal:
        fa_due = _d(first_appeal, FA_DECISION_DAYS)
        dates.update(first_appeal_filed=first_appeal, fa_decision_due=fa_due,
                     fa_decision_latest=_d(first_appeal, FA_DECISION_MAX_DAYS))
        base = fa_decided or fa_due
        s_deadline = _d(base, SECOND_APPEAL_DAYS)
        dates["second_appeal_deadline"] = s_deadline
        if fa_decided or today > fa_due:
            if today <= s_deadline:
                out.update(stage="second_appeal_open", can_second_appeal=True,
                           reason="decided" if fa_decided else "fa_overdue")
            else:
                out.update(stage="second_appeal_closed", reason="second_deadline_passed")
        else:
            out.update(stage="first_appeal_pending", reason="fa_in_time")
    elif transferred_physically:
        out.update(stage="blocked_transfer", reason="transferred")
    elif not replied and today <= reply_due:
        out.update(stage="waiting_reply", reason="reply_not_due")
    elif today > fa_close:
        out.update(stage="first_appeal_closed", reason="first_deadline_passed")
    else:
        out.update(stage="first_appeal_open", can_first_appeal=True,
                   reason="replied" if replied else "no_reply")

    out["dates"] = {k: v.isoformat() for k, v in dates.items()}
    out["days_left"] = {
        "reply_due": (reply_due - today).days,
        "first_appeal_opens": (fa_open - today).days,
        "first_appeal_deadline": (fa_close - today).days,
    }
    if "second_appeal_deadline" in dates:
        out["days_left"]["second_appeal_deadline"] = (dates["second_appeal_deadline"] - today).days
        out["days_left"]["fa_decision_due"] = (dates["fa_decision_due"] - today).days
    return out
