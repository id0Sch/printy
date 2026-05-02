"""FastMCP server exposing printy as MCP tools/prompts/resources."""
from __future__ import annotations

from fastmcp import FastMCP

from . import db
from .render import print_submission

mcp = FastMCP("printy")


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
    sub_id = db.insert_submission(sender, subject, body)
    try:
        print_submission(sender, subject, body)
    except Exception as exc:
        db.mark_status(sub_id, "failed", str(exc))
        raise
    db.mark_status(sub_id, "printed")
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
    return """\
PRINTY THERMAL PRINTER SPEC

Hardware: MIAOBAO 58Printer (58mm thermal, USB)
Paper width: 32 chars per line in Font A (used by default)
Auto-cutter: NO — receipts feed 3 blank lines and are torn off by hand

Supported ESC/POS formatting:
- bold, underline, center/left/right alignment
- font A (default, 32 cols), font B (smaller, ~50 cols but ugly)
- QR codes via escpos (used in test_print only)

NOT supported / unreliable:
- double-width text (consumes columns, often wraps mid-letter)
- images / graphics (technically work via escpos but slow over USB)
- cut command (printer ignores it — no auto-cutter)
- right alignment looks awkward on 32 cols, prefer center or left

Formatting rules for body text:
1. The render layer wraps body lines to 32 chars on word boundaries.
   You don't need to pre-wrap, BUT if you want columns to line up
   (e.g. time + event), pre-format with spaces and keep each line ≤32 chars.
2. Use "-" * 32 or "=" * 32 as separators — they're already used
   automatically around the title and at the end.
3. Don't put long unbreakable tokens (URLs, hashes) — they'll get
   chopped mid-character. Truncate or use a QR code instead.
4. Newlines in the body are preserved. Use them to make sections.
5. Subject is auto-centered, bold. Keep ≤32 chars or it wraps.

Stylistic conventions used in this household:
- Calendar prints: time on left (5 chars HH:MM), 2 spaces, then event.
- Alert prints: severity in [BRACKETS] on its own line above the body.
- Restaurant-order prints: ">> SECTION  [tag]" headers, "  - bullet" items.
"""


@mcp.prompt
def format_alert(severity: str, title: str, body: str) -> str:
    """Format an alert/incident as a printable receipt body.

    severity: e.g. "P0", "HIGH", "WARNING", "INFO"
    title: short headline
    body: details (will be wrapped to 32 cols)
    """
    return f"""\
Format this as a printy receipt for an alert. Use these fields when calling print_message:

- sender: the source system (e.g. "Datadog", "PostHog", "monitor")
- subject: "{title}" (bold, centered, ≤32 chars — shorten if needed)
- body: format like this (one [SEVERITY] line, blank line, then details):

[{severity.upper()}]

{body}

Then call print_message(sender=..., subject=..., body=<the above>)."""


@mcp.prompt
def format_restaurant_order(title: str, items: str) -> str:
    """Format a list of items as a restaurant-order ticket.

    title: order title (becomes subject), e.g. "ORDER #18287"
    items: the items to print, freeform — the prompt explains the layout
    """
    return f"""\
Format this as a restaurant-order receipt for printy. Group items by course
(APPETIZER / MAIN COURSE / SIDE / DESSERT) and tag each with a "spice level"
that maps to severity or priority.

Use these exact patterns in the body:

>> APPETIZER  [HIGH SPICE]
Item name au gratin
  - detail bullet 1
  - detail bullet 2
  - file: path/to/file.ext L42

>> MAIN COURSE  [mild]
Another item
  - ...

End with a footer line counting items and bon appetit. Keep every line ≤32 chars.

Items to format:
{items}

Then call print_message(sender="Table <user>", subject="*** {title} ***", body=<the formatted body>)."""


@mcp.prompt
def format_calendar(date: str, events: str) -> str:
    """Format a calendar day as a printable schedule.

    date: e.g. "Sun May 3"
    events: freeform list of events (the prompt explains layout)
    """
    return f"""\
Format this calendar day as a printy receipt.

Layout rules:
- Subject: short date like "{date}" (≤32 chars)
- All-day events first, prefixed with "all-day:" header and "- " bullets
- Then a separator line of 32 dashes
- Then timed events, one per line: "HH:MM  Event name"
  - HH:MM is 5 chars, two spaces, then event (≤25 chars; truncate if longer)
  - Mark declined events with "(decl.)" suffix
  - Mark OOO/personal time with "(OOO)" suffix
- Keep every line ≤32 chars

Events to format:
{events}

Then call print_message(sender="calendar", subject="{date}", body=<formatted>)."""
