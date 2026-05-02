"""Shared print-and-persist path used by both the REST handler and MCP tool.

Owns the global lock that serializes access to the single-claim USB device,
so REST and MCP callers can't race each other.
"""

from __future__ import annotations

import logging
import threading

from . import db
from .render import print_submission

log = logging.getLogger("printy")

# Single lock for all callers (REST, MCP, future schedulers).
_print_lock = threading.Lock()


class PrintError(RuntimeError):
    """Raised when the underlying ESC/POS print call fails. The submission
    is already persisted with status='failed' before this is raised."""

    def __init__(self, submission_id: int, original: BaseException) -> None:
        super().__init__(str(original))
        self.submission_id = submission_id
        self.original = original


def submit_and_print(
    sender: str,
    subject: str,
    body: str,
    requester: str | None = None,
) -> int:
    """Persist a submission, print it under the shared lock, return the id.

    `requester` is the tailnet identity from Tailscale-User-* headers when
    available, used for the audit column and stamped onto the receipt.

    On printer error, marks the row 'failed' and raises PrintError so the
    caller can map it to its own protocol's error response.
    """
    sub_id = db.insert_submission(sender, subject, body, requester=requester)
    with _print_lock:
        try:
            print_submission(sender, subject, body, requester=requester)
        except Exception as exc:
            log.exception("print failed for submission %s", sub_id)
            db.mark_status(sub_id, "failed", str(exc))
            raise PrintError(sub_id, exc) from exc
        db.mark_status(sub_id, "printed")
    return sub_id
