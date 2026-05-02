# printy backend — setup

Two roles: the **printer-host** (laptop with the USB printer plugged in, runs the
backend) and **clients** (any laptop where you use Claude Code and want to print).

## Printer-host setup (one-time)

Plug the USB thermal printer in, then:

```bash
# 1. System deps
brew install libusb uv

# 2. Get the code
git clone git@github.com:id0Sch/printy.git ~/dev/printy
cd ~/dev/printy
uv sync

# 3. Smoke test
uv run python -m backend            # starts on :7777
# in another terminal:
curl http://127.0.0.1:7777/printy/health   # → {"status":"ok"}
curl -X POST http://127.0.0.1:7777/printy/print \
    -H 'Content-Type: application/json' \
    -d '{"from":"setup","subject":"hello","body":"test print"}'
# Paper should come out.
```

Stop the foreground server (Ctrl-C). Now make it auto-start:

```bash
# 4. Install launchd plist (replace placeholders, copy, load)
sed "s|__HOME__|$HOME|g" backend/launchd/co.printy.backend.plist \
    > ~/Library/LaunchAgents/co.printy.backend.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/co.printy.backend.plist

# Verify it's running
launchctl print gui/$UID/co.printy.backend | grep state
curl http://127.0.0.1:7777/printy/health
```

Logs land in `~/dev/id0sch/printy/printy.{stdout,stderr}.log`.

## Expose to the tailnet

Tailscale must already be installed and authed on this machine
(`tailscale status` to check).

```bash
# Forward https://<host>.<tailnet>.ts.net/printy/* → http://127.0.0.1:7777/printy/*
sudo tailscale serve --bg --set-path /printy http://127.0.0.1:7777/printy

# Verify
tailscale serve status
HOST=$(tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')
curl https://$HOST/printy/health   # → {"status":"ok"}
```

The `tailscale serve` config persists across reboots — no launchd needed for it.

To remove the exposure later:
```bash
sudo tailscale serve --set-path /printy off
```

## Client setup (every laptop you want to print from)

```bash
# Find the printer-host's tailnet hostname (run on the printer-host, or look it up
# via the Tailscale admin console). Example: printer-mac.tail-foo.ts.net

claude mcp add --transport http --scope user printy \
    https://<printer-host>.<tailnet>.ts.net/printy/mcp/

# Verify
claude mcp list | grep printy
```

After that, any new Claude Code session has the `print_message`, `list_recent`,
and `get_submission` tools, plus the `format_alert`, `format_restaurant_order`,
and `format_calendar` prompts.

## Troubleshooting

- **`USB device not found`** in logs: printer unplugged or asleep. Replug it,
  the backend will work on the next request (no restart needed — it opens
  per-request).
- **`tailscale serve` says "no certs"**: machine not authed yet. Run `tailscale
  up` first.
- **MCP tools not visible in Claude Code**: registered after the session
  started. Run `/mcp reconnect` or start a new session.
- **launchd job won't start / immediately exits**: check
  `~/dev/printy/printy.stderr.log`. Common cause: working dir wrong (the
  plist hardcodes `~/dev/printy` — if you cloned elsewhere, edit the plist
  and `launchctl bootout` + `bootstrap` again). Inspect with:
  `launchctl print gui/$UID/co.printy.backend | grep -E 'state|last exit'`.
- **Want to also print from the printer-host itself?** It already works —
  `claude mcp add` with `http://127.0.0.1:7777/printy/mcp/` (no tailscale).
