"""Deadline reminders for a submitted RTI. Computed from the submission date; nothing is sent in this demo."""
from datetime import date, timedelta

from . import appeal


def for_request(submitted: date, today: date) -> list[dict]:
    due = submitted + timedelta(days=appeal.REPLY_DAYS)
    items = [
        ("reply_soon", due - timedelta(days=5), "Reply due soon", "The office should reply by {d3}."),
        ("appeal_opens", due + timedelta(days=1), "First appeal opens", "If there is no reply, you can file a first appeal from {d}."),
        ("appeal_closing", due + timedelta(days=appeal.FIRST_APPEAL_DAYS - 7), "First appeal closing", "The usual window ends in 7 days, on {d2}."),
    ]
    out = []
    for kind, when, title, text in items:
        deadline = due + timedelta(days=appeal.FIRST_APPEAL_DAYS)
        out.append({"kind": kind, "date": when.isoformat(), "title": title,
                    "text": text.format(d=when.isoformat(), d2=deadline.isoformat(), d3=due.isoformat()),
                    "state": "due" if when == today else "past" if when < today else "upcoming",
                    "days": (when - today).days})
    return out
