"""Tests for db.py against a temporary SQLite file (no printer needed)."""

import importlib

import pytest

from backend import db


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Point DB_PATH at a temp file, recreate schema, yield the module."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    importlib.reload(db)  # pick up the patched DB_PATH in connect()
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init()
    yield db


def test_insert_and_get_roundtrip(fresh_db):
    sub_id = fresh_db.insert_submission("alice", "subject", "body text")
    row = fresh_db.get_submission(sub_id)
    assert row["sender"] == "alice"
    assert row["subject"] == "subject"
    assert row["body"] == "body text"
    assert row["status"] == "pending"
    assert row["error"] is None
    assert row["created_at"]  # iso string


def test_mark_status_printed(fresh_db):
    sub_id = fresh_db.insert_submission("a", "b", "c")
    fresh_db.mark_status(sub_id, "printed")
    assert fresh_db.get_submission(sub_id)["status"] == "printed"


def test_mark_status_failed_records_error(fresh_db):
    sub_id = fresh_db.insert_submission("a", "b", "c")
    fresh_db.mark_status(sub_id, "failed", "USB went away")
    row = fresh_db.get_submission(sub_id)
    assert row["status"] == "failed"
    assert row["error"] == "USB went away"


def test_get_submission_missing(fresh_db):
    assert fresh_db.get_submission(99999) is None


def test_list_submissions_newest_first(fresh_db):
    ids = [fresh_db.insert_submission(f"u{i}", "s", "b") for i in range(3)]
    rows = fresh_db.list_submissions()
    assert [r["id"] for r in rows] == list(reversed(ids))


def test_list_submissions_respects_limit(fresh_db):
    for i in range(5):
        fresh_db.insert_submission(f"u{i}", "s", "b")
    assert len(fresh_db.list_submissions(limit=2)) == 2


def test_reap_stale_pending(fresh_db):
    """A pending row older than the cutoff should flip to 'lost'."""
    sub_id = fresh_db.insert_submission("a", "b", "c")
    # Manually backdate it past the default 5-minute cutoff.
    with fresh_db.connect() as c:
        c.execute(
            "UPDATE submissions SET created_at = ? WHERE id = ?",
            ("2020-01-01T00:00:00+00:00", sub_id),
        )
    reaped = fresh_db.reap_stale_pending()
    assert reaped == 1
    row = fresh_db.get_submission(sub_id)
    assert row["status"] == "lost"


def test_reap_leaves_recent_pending_alone(fresh_db):
    sub_id = fresh_db.insert_submission("a", "b", "c")
    reaped = fresh_db.reap_stale_pending()
    assert reaped == 0
    assert fresh_db.get_submission(sub_id)["status"] == "pending"


def test_reap_ignores_non_pending(fresh_db):
    sub_id = fresh_db.insert_submission("a", "b", "c")
    fresh_db.mark_status(sub_id, "printed")
    with fresh_db.connect() as c:
        c.execute(
            "UPDATE submissions SET created_at = ? WHERE id = ?",
            ("2020-01-01T00:00:00+00:00", sub_id),
        )
    assert fresh_db.reap_stale_pending() == 0
