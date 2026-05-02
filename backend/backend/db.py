"""SQLite persistence for print submissions. Stdlib only."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

# DB lives at the workspace root so future sibling projects share it.
DB_PATH = Path(__file__).resolve().parents[2] / "printy.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    sender      TEXT NOT NULL,
    subject     TEXT NOT NULL,
    body        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    error       TEXT
);
CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at);
"""


def init() -> None:
    with connect() as c:
        c.executescript(SCHEMA)


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def insert_submission(sender: str, subject: str, body: str) -> int:
    with connect() as c:
        cur = c.execute(
            "INSERT INTO submissions (created_at, sender, subject, body) VALUES (?, ?, ?, ?)",
            (datetime.now(UTC).isoformat(), sender, subject, body),
        )
        return cur.lastrowid


def mark_status(submission_id: int, status: str, error: str | None = None) -> None:
    with connect() as c:
        c.execute(
            "UPDATE submissions SET status = ?, error = ? WHERE id = ?",
            (status, error, submission_id),
        )


def get_submission(submission_id: int) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
        return dict(row) if row else None


def list_submissions(limit: int = 50) -> list[dict]:
    with connect() as c:
        rows = c.execute("SELECT * FROM submissions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
