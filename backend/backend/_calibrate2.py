"""Print rulers without text-wrapping to see the device's real column count.

Sends ESC/POS font-select control bytes by interleaving them with text(),
which escpos passes through unchanged. No private-API access needed.
"""

from .printer import open_printer


def main() -> None:
    with open_printer() as p:
        p.text("\x1b@")  # ESC @ : init
        p.text("\x1bM\x00")  # ESC M 0 : Font A
        p.text("Font A raw 50:\n")
        p.text("12345678901234567890123456789012345678901234567890\n")
        p.text("\x1bM\x01")  # ESC M 1 : Font B
        p.text("Font B raw 60:\n")
        p.text("123456789012345678901234567890123456789012345678901234567890\n")
        p.text("\n\n\n")


if __name__ == "__main__":
    main()
