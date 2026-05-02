"""Read Tailscale identity headers injected by `tailscale serve`.

These headers identify the human on the tailnet making the request:

    Tailscale-User-Login        e.g. "alice@example.com"
    Tailscale-User-Name         e.g. "Alice Architect"
    Tailscale-User-Profile-Pic  URL (we ignore this)

Headers only arrive for tailnet traffic (not Funnel) and not from tagged
devices. The backend is bound to 127.0.0.1 so headers can't be spoofed
from the LAN — the only way they reach us is through tailscale serve.

See https://tailscale.com/docs/features/tailscale-serve#identity-headers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TailscaleUser:
    login: str
    name: str

    def short(self) -> str:
        """Short label for display: 'Name (login)' or just one if equal/missing."""
        if self.name and self.name != self.login:
            return f"{self.name} ({self.login})"
        return self.login or self.name


def from_headers(headers: Mapping[str, str]) -> TailscaleUser | None:
    """Pull a TailscaleUser out of HTTP headers, or None if not present.

    Header lookup is case-insensitive (FastAPI/Starlette's headers dict is).
    """
    login = headers.get("tailscale-user-login") or headers.get("Tailscale-User-Login") or ""
    name = headers.get("tailscale-user-name") or headers.get("Tailscale-User-Name") or ""
    if not login and not name:
        return None
    return TailscaleUser(login=login, name=name)
