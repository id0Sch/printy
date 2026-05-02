"""Tests for the Tailscale identity header parser."""

from backend.identity import TailscaleUser, from_headers


def test_from_headers_full():
    user = from_headers(
        {
            "Tailscale-User-Login": "alice@example.com",
            "Tailscale-User-Name": "Alice Example",
        }
    )
    assert user == TailscaleUser(login="alice@example.com", name="Alice Example")
    assert user.short() == "Alice Example (alice@example.com)"


def test_from_headers_login_only():
    user = from_headers({"Tailscale-User-Login": "alice@example.com"})
    assert user.login == "alice@example.com"
    assert user.name == ""
    assert user.short() == "alice@example.com"


def test_from_headers_name_equals_login():
    """Don't render 'foo (foo)' if name and login are identical."""
    user = from_headers({"Tailscale-User-Login": "alice", "Tailscale-User-Name": "alice"})
    assert user.short() == "alice"


def test_from_headers_case_insensitive():
    user = from_headers({"tailscale-user-login": "alice"})
    assert user is not None
    assert user.login == "alice"


def test_from_headers_missing_returns_none():
    assert from_headers({}) is None
    assert from_headers({"X-Other": "value"}) is None
