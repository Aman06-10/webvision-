import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  draft TEXT NOT NULL DEFAULT '',
  source_lang TEXT NOT NULL DEFAULT 'en',
  original_text TEXT NOT NULL DEFAULT '',
  authority_key TEXT,
  authority_confirmed INTEGER NOT NULL DEFAULT 0,
  state TEXT NOT NULL DEFAULT 'DRAFT',
  rti_number TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id INTEGER NOT NULL REFERENCES applications(id),
  idem_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL,
  amount INTEGER NOT NULL,
  scenario TEXT NOT NULL DEFAULT 'success',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
-- one live payment per application, enforced by the database
CREATE UNIQUE INDEX IF NOT EXISTS one_active_payment
  ON payments(application_id) WHERE status IN ('INITIATED','PENDING','PAID');
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  detail TEXT NOT NULL DEFAULT '',
  at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect() -> sqlite3.Connection:
    c = sqlite3.connect(config.DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


@contextmanager
def tx():
    c = connect()
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init() -> None:
    with tx() as c:
        c.executescript(SCHEMA)


def log_event(c: sqlite3.Connection, app_id: int, kind: str, detail: str = "") -> None:
    c.execute("INSERT INTO events(application_id, kind, detail) VALUES (?,?,?)",
              (app_id, kind, detail))
