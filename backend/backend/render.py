"""Render a (from, subject, body) submission to the thermal printer."""
from __future__ import annotations

import textwrap
from datetime import datetime

from .printer import open_printer

LINE_WIDTH = 32  # MIAOBAO 58Printer fits 32 chars in Font A


def _hr(char: str = "-") -> str:
    return char * LINE_WIDTH + "\n"


def _wrap(text: str, width: int = LINE_WIDTH) -> str:
    out_lines: list[str] = []
    for raw in (text or "").splitlines() or [""]:
        if not raw:
            out_lines.append("")
            continue
        wrapped = textwrap.wrap(
            raw,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        out_lines.extend(wrapped or [""])
    return "\n".join(out_lines) + "\n"


def print_submission(sender: str, subject: str, body: str) -> None:
    with open_printer() as p:
        p.set(font="a", align="center", bold=True)
        p.text(_wrap(subject or "(no subject)"))
        p.set(font="a", align="left", bold=False)
        p.text(_wrap(f"from: {sender}"))
        p.text(datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")
        p.text(_hr("="))

        p.text(_wrap((body or "").rstrip()))
        p.text(_hr())
        p.ln(3)
