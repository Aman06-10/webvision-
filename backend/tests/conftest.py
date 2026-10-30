import pytest

from app import config, db, gateway


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    gateway._txns.clear()
    t = {"now": 1000.0}
    monkeypatch.setattr(gateway, "clock", lambda: t["now"])
    db.init()
    return t


def make_app(authority=True, draft="Please share the file notings."):
    with db.tx() as c:
        cur = c.execute("INSERT INTO applications(email, draft, authority_confirmed) "
                        "VALUES ('a@b.c', ?, ?)", (draft, int(authority)))
        return cur.lastrowid


def state(app_id):
    with db.tx() as c:
        return dict(c.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone())
