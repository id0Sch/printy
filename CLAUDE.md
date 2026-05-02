# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A backend for a USB thermal receipt printer (MIAOBAO 58Printer, vendor `0x0483`, product `0x5840`). One service exposes both:
- a small **REST API** (`POST /printy/print`, `GET /printy/health`, `GET /printy/submissions`) for curl/web clients
- an **MCP server** (`/printy/mcp/`, FastMCP over HTTP) so Claude Code agents can print directly via tool calls

Designed to live behind `tailscale serve --set-path /printy` on a printer-host laptop, with clients connecting from anywhere on the tailnet. See `backend/SETUP.md` for the printer-host install path.

## Layout

This is a **uv workspace** (`pyproject.toml` at root declares members). Today there's one member: `backend/`. The shape (workspace + member with own `pyproject.toml`) is intentional — sibling projects (calendar-printer, alert-router, etc.) get added as new workspace members, not crammed into `backend/`.

Inside `backend/backend/`:
- `api.py` — FastAPI. Two apps: `printy_app` holds the REST routes and mounts MCP at `/mcp`. The outer `app` mounts `printy_app` at `/printy`. **Lifespan must live on the outer `app`** — that's where uvicorn enters and where FastMCP's `StreamableHTTPSessionManager` task group gets initialized. Moving it to `printy_app` will make MCP requests 500.
- `mcp_server.py` — three tools (`print_message`, `list_recent`, `get_submission`), one resource (`printy://printer`), two prompts (`format_alert`, `format_calendar`). The resource and prompt bodies live as `backend/backend/prompts/*.md` and are loaded via `importlib.resources`. Edit the markdown, not the code, for content tweaks.
- `printer.py` — USB connection. `open_printer()` claims the device for the duration of one print job (single-claim, so concurrent prints serialize). `is_connected()` is a cheap presence check that does not claim the device — used by `/health`.
- `render.py` — formats `(sender, subject, body)` into ESC/POS calls. **All wrapping happens here at 32 chars/line** (Font A on this hardware). Body lines are word-wrapped by `textwrap`. Any new render layouts should go through `_wrap()`.
- `db.py` — sqlite3 stdlib only. Single `submissions` table. The DB file (`printy.db`) lives at the **workspace root** so future sibling projects can read it.
- `test_print.py`, `_calibrate*.py`, `_inspect.py` — manual diagnostic scripts. Run with `uv run python -m backend.test_print` etc. when debugging the physical printer.

## Hardware constraints to remember

The MIAOBAO 58Printer is **32 chars wide in Font A** (Font B exists but is uglier; calibration tests confirmed Font A at 32 cols looks best). It has **no auto-cutter** — `p.cut()` is a no-op; `render.py` instead feeds 3 blank lines (`p.ln(3)`) so paper can be torn off. Don't add `cut()` calls. Don't use `double_width` (consumes columns, wraps mid-letter on this device).

The printer is USB-only. We tried Bluetooth — see git log around the BT detour — macOS BT-SPP idle-disconnects this printer's RFCOMM channel and writes go silently into the void. Don't reintroduce a BT path on macOS without an `rfcomm bind`-equivalent (only Linux has that).

## Path prefix gotcha

Everything is wrapped under `/printy/` so the whole API can be exposed via `tailscale serve --set-path /printy http://127.0.0.1:7777/printy` end-to-end with no path stripping. If you add a route, attach it to `printy_app` (not `app`) so it ends up at `/printy/<route>`.

## Common commands

```bash
# from workspace root
uv sync                                 # install everything
uv run python -m backend                # run the server on :7777
uv run ruff format backend/             # format
uv run ruff check --fix backend/        # lint with auto-fix

# end-to-end smoke test
curl http://127.0.0.1:7777/printy/health
curl -X POST http://127.0.0.1:7777/printy/print \
    -H 'Content-Type: application/json' \
    -d '{"from":"test","subject":"hi","body":"hello"}'

# manual printer diagnostics (each opens the USB device)
uv run python -m backend.test_print     # full smoke receipt
uv run python -m backend._calibrate2    # raw ESC/POS column ruler
uv run python -m backend._inspect       # USB descriptor dump
```

There are no automated tests yet. Verification is "did paper come out, does it look right" — see git history for photos of failures and fixes.

## Hooks

`lefthook.yml` wires up:
- `pre-commit` — ruff format + `ruff check --fix` on staged `*.py`, re-stages on change.
- `pre-push` — `ruff format --check` and `ruff check` over `backend/`. Push fails if either does.

Run `lefthook install` once after cloning. CI is not configured; the pre-push hook is the safety net.

## Adding a new sibling project

1. `mkdir <name> && cd <name> && uv init` (or copy `backend/pyproject.toml` as a template).
2. Add `"<name>"` to `members` in the root `pyproject.toml`.
3. `uv sync` from the workspace root.
4. The project can `from backend import db` if you add `backend` as a workspace dep, but prefer hitting the HTTP API at `http://127.0.0.1:7777/printy/...` — keeps coupling loose.

## When things break

- `/health` returns 503 with `printer: missing` → printer unplugged or asleep. Replug. The backend opens USB per-request, no restart needed.
- `RuntimeError: FastMCP's StreamableHTTPSessionManager task group was not initialized` → lifespan is on the wrong FastAPI app. Must be on the outermost (`app`, not `printy_app`).
- `Invalid endpoint address 0x1` → escpos's default profile is wrong for this printer. The fix is the explicit `in_ep=0x82, out_ep=0x04` already in `printer.py`. Don't override.
- `usb.core.NoBackendError` on macOS → libusb not installed or not findable. `brew install libusb`. The `_libusb_backend()` helper looks at `/opt/homebrew/lib` and `/usr/local/lib`; set `LIBUSB_PATH` to override.
