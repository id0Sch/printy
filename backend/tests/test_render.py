"""Tests for the pure rendering helpers.

print_submission itself touches USB and isn't unit-testable here; we cover
the wrap helper which is where every formatting bug lives.
"""

from backend.render import LINE_WIDTH, _wrap


def test_wrap_short_line_unchanged():
    assert _wrap("hello") == "hello\n"


def test_wrap_breaks_on_word_boundary():
    text = "this is a sentence that needs wrapping at thirty-two cols"
    out = _wrap(text)
    for line in out.rstrip("\n").split("\n"):
        assert len(line) <= LINE_WIDTH, f"line too long: {line!r}"
    # Original words must all be preserved.
    assert set(out.split()) == set(text.split())


def test_wrap_preserves_explicit_newlines():
    out = _wrap("line one\nline two\n\nline four")
    lines = out.rstrip("\n").split("\n")
    assert lines == ["line one", "line two", "", "line four"]


def test_wrap_breaks_unbreakable_long_token():
    # A 50-char no-space token must still be broken to fit the line width.
    token = "x" * 50
    out = _wrap(token)
    for line in out.rstrip("\n").split("\n"):
        assert len(line) <= LINE_WIDTH


def test_wrap_empty_input():
    assert _wrap("") == "\n"


def test_wrap_only_newlines():
    # splitlines("\n\n") = ["", ""] → joined with "\n" + trailing "\n"
    assert _wrap("\n\n") == "\n\n"
