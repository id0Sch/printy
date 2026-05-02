# printy

A small backend that prints text on a USB thermal receipt printer (the cheap
58mm "MIAOBAO 58Printer" you can find for $20 on AliExpress). Speaks two
protocols on the same port:

- **REST**: `POST /printy/print` with `{from, subject, body}` and a receipt
  comes out.
- **MCP** (Model Context Protocol): three tools (`print_message`,
  `list_recent`, `get_submission`), one resource (`printy://printer`), and
  prompts for formatting alerts and calendars. Designed to be added as an
  MCP server in Claude Code or any other MCP client, so an agent can print
  things on its own without going through curl.

Built so you can run the backend on one laptop with the printer plugged in,
expose it via [Tailscale](https://tailscale.com), and print from anywhere on
your tailnet.

## What it looks like

```
┌──────────────────────────────────┐
│        bugbot order #18287       │
│                                  │
│ from: Cursor Bugbot              │
│ 2026-04-14 10:35                 │
│ ================================ │
│ >> APPETIZER  [HIGH SPICE]       │
│ Timezone TypeError au gratin     │
│   - aware vs naive on /api/me    │
│   - file: routes/me.py L46       │
│ ...                              │
└──────────────────────────────────┘
```

(yes, real receipt, real bug.)

## Quick start (local)

```bash
brew install libusb uv
git clone git@github.com:id0Sch/printy.git
cd printy
uv sync

# plug printer in via USB, then:
uv run python -m backend
```

In another terminal:

```bash
curl -X POST http://127.0.0.1:7777/printy/print \
    -H 'Content-Type: application/json' \
    -d '{"from":"me","subject":"hello","body":"first print"}'
```

If paper comes out, you're set.

## Wire it into Claude Code (MCP)

```bash
claude mcp add --transport http --scope user printy http://127.0.0.1:7777/printy/mcp/
```

Restart your Claude Code session. The agent now has `print_message`,
`list_recent`, and `get_submission` tools, plus prompts for alerts and
calendars. Ask it to "print my calendar for tomorrow" or "print this PR as
a restaurant order" and it figures out the rest.

## Run on a separate "printer host"

If you want to leave one laptop plugged into the printer and use it from
others, see [`backend/SETUP.md`](./backend/SETUP.md). The short version:

1. Install on the printer-host (same as Quick start above).
2. Auto-start on login: copy `backend/launchd/co.printy.backend.plist` to
   `~/Library/LaunchAgents/`, `launchctl bootstrap` it.
3. Expose over the tailnet:
   ```bash
   sudo tailscale serve --bg --set-path /printy http://127.0.0.1:7777/printy
   ```
4. From any client laptop:
   ```bash
   claude mcp add --transport http --scope user printy \
       https://<host>.<tailnet>.ts.net/printy/mcp/
   ```

Tailscale-only. The backend never binds to `0.0.0.0`, so nothing on the LAN
sees it; tailnet membership is the auth.

## Endpoints

All under `/printy/`:

| Method | Path                       | Notes                                                 |
| ------ | -------------------------- | ----------------------------------------------------- |
| GET    | `/printy/health`           | `200 ok` if printer plugged in, `503 degraded` if not |
| POST   | `/printy/print`            | `{from, subject, body}` → prints + persists           |
| GET    | `/printy/submissions`      | recent print jobs (newest first)                      |
| GET    | `/printy/submissions/{id}` | one job by id                                         |
| any    | `/printy/mcp/`             | MCP over HTTP (stream)                                |

Submissions persist in `printy.db` (sqlite) at the repo root.

## Hardware

Tested with a generic 58mm thermal printer (USB ID `0483:5840`, often sold as
"MIAOBAO 58Printer", "ZJ-58", or unbranded). 32 chars per line in Font A,
no auto-cutter — paper feeds 3 lines so you can tear it. Different printers
will need their USB IDs and endpoints adjusted in
[`backend/backend/printer.py`](./backend/backend/printer.py); the
`_inspect.py` helper dumps the descriptors you need.

Bluetooth: don't bother on macOS. The RFCOMM channel idle-disconnects and
writes vanish. Linux `rfcomm bind` works, but no path on macOS that's worth
the headache.

## Development

```bash
uv run ruff format backend/        # format
uv run ruff check --fix backend/   # lint
lefthook install                   # one-time, wires up pre-commit + pre-push
```

Architecture notes for contributors and AI agents live in
[`CLAUDE.md`](./CLAUDE.md).

## License

No license yet. If you want to use this somewhere serious, open an issue.
