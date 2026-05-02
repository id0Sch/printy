"""FastMCP server exposing printy as MCP tools/prompts/resources.

Prompt and resource bodies live as markdown under ./prompts/ — easier to edit
without touching code. They use {placeholder} interpolation via str.format.
"""

from __future__ import annotations

from importlib.resources import files

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from . import db
from .identity import from_headers
from .service import submit_and_print

mcp = FastMCP("printy")

_PROMPTS = files(__package__) / "prompts"


def _load(name: str) -> str:
    return (_PROMPTS / name).read_text(encoding="utf-8")


@mcp.tool
def print_message(sender: str, subject: str, body: str) -> dict:
    """Print a receipt on the thermal printer and persist the submission.

    Args:
        sender: Who the message is from (e.g. "calendar", "monitor", "alice").
                Shown on the receipt as "from: <sender>". 1-120 chars.
        subject: Bold title line at the top of the receipt. 1-200 chars.
        body: The main content. Wrapped to 32 chars per line on word boundaries.
              Newlines in the body are preserved. 1-10000 chars.

    Returns:
        {"id": <int>, "status": "printed"} on success.
    """
    user = from_headers(get_http_headers())
    requester = user.short() if user else None
    sub_id = submit_and_print(sender, subject, body, requester=requester)
    return {"id": sub_id, "status": "printed"}


@mcp.tool
def list_recent(limit: int = 20) -> list[dict]:
    """List the most recent print submissions, newest first."""
    return db.list_submissions(limit=limit)


@mcp.tool
def get_submission(submission_id: int) -> dict | None:
    """Fetch a single submission by id, or None if not found."""
    return db.get_submission(submission_id)


@mcp.resource("printy://printer")
def printer_spec() -> str:
    """Specs and formatting rules for the thermal printer."""
    return _load("printer_spec.md")


@mcp.prompt
def format_alert(severity: str, title: str, body: str) -> str:
    """Format an alert/incident as a printable receipt body.

    severity: e.g. "P0", "HIGH", "WARNING", "INFO"
    title: short headline
    body: details (will be wrapped to 32 cols)
    """
    return _load("format_alert.md").format(
        severity_upper=severity.upper(),
        title=title,
        body=body,
    )


@mcp.prompt
def format_calendar(date: str, events: str) -> str:
    """Format a calendar day as a printable schedule.

    date: e.g. "Sun May 3"
    events: freeform list of events (the prompt explains layout)
    """
    return _load("format_calendar.md").format(date=date, events=events)
