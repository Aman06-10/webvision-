from datetime import date, timedelta

import pytest

from app import appeal

F = date(2026, 1, 1)


def at(days, **kw):
    return appeal.assess(F, F + timedelta(days=days), **kw)


def test_waiting_for_reply_inside_30_days():
    r = at(10)
    assert r["stage"] == "waiting_reply" and not r["can_first_appeal"]
    assert r["days_left"]["reply_due"] == 20 and r["dates"]["reply_due"] == "2026-01-31"


def test_day_30_is_still_waiting_day_31_opens():
    assert at(30)["stage"] == "waiting_reply"
    r = at(31)
    assert r["stage"] == "first_appeal_open" and r["reason"] == "no_reply" and r["can_first_appeal"]


def test_no_reply_window_closes_60_days_in():
    assert at(60)["stage"] == "first_appeal_open"
    r = at(61)
    assert r["stage"] == "first_appeal_closed" and not r["can_first_appeal"]


def test_reply_received_gives_30_days_from_reply():
    r = at(40, replied=F + timedelta(days=20))
    assert r["can_first_appeal"] and r["reason"] == "replied"
    assert r["dates"]["first_appeal_deadline"] == (F + timedelta(days=50)).isoformat()
    assert at(51, replied=F + timedelta(days=20))["stage"] == "first_appeal_closed"


def test_reply_makes_appeal_possible_before_day_30():
    assert at(15, replied=F + timedelta(days=10))["can_first_appeal"]


def test_physical_transfer_blocks_online_appeal():
    r = at(45, transferred_physically=True)
    assert r["stage"] == "blocked_transfer" and not r["can_first_appeal"]


def test_first_appeal_pending_until_45_days_then_second_appeal_opens():
    fa = F + timedelta(days=40)
    assert appeal.assess(F, fa + timedelta(days=10), first_appeal=fa)["stage"] == "first_appeal_pending"
    assert appeal.assess(F, fa + timedelta(days=45), first_appeal=fa)["stage"] == "first_appeal_pending"  # CIC: after 45 days
    r = appeal.assess(F, fa + timedelta(days=46), first_appeal=fa)
    assert r["stage"] == "second_appeal_open" and r["can_second_appeal"] and r["reason"] == "fa_overdue"
    assert r["dates"]["second_appeal_opens"] == (fa + timedelta(days=46)).isoformat()
    assert r["dates"]["second_appeal_deadline"] == (fa + timedelta(days=135)).isoformat()  # 45 + 90


def test_second_appeal_after_decision_and_deadline():
    fa, dec = F + timedelta(days=40), F + timedelta(days=60)
    r = appeal.assess(F, dec, first_appeal=fa, fa_decided=dec)  # opens the same day the decision arrives
    assert r["can_second_appeal"] and r["reason"] == "decided"
    assert r["dates"]["second_appeal_deadline"] == (dec + timedelta(days=90)).isoformat()
    assert appeal.assess(F, dec + timedelta(days=90), first_appeal=fa, fa_decided=dec)["can_second_appeal"]
    r = appeal.assess(F, dec + timedelta(days=91), first_appeal=fa, fa_decided=dec)
    assert r["stage"] == "second_appeal_closed" and not r["can_second_appeal"]


def test_bad_dates_rejected():
    with pytest.raises(ValueError):
        appeal.assess(F, F - timedelta(days=1))
    with pytest.raises(ValueError):
        appeal.assess(F, F + timedelta(days=5), replied=F - timedelta(days=1))
    with pytest.raises(ValueError):
        appeal.assess(F, F + timedelta(days=5), replied=F + timedelta(days=9))
