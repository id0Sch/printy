"""Try printing rulers without text wrapping by sending raw ESC/POS.
This bypasses the python-escpos profile so we see the device's real column count.
"""
from .printer import open_printer


def main() -> None:
    with open_printer() as p:
        # Reset, Font A
        p._raw(b"\x1b@")  # ESC @ : init
        p._raw(b"\x1bM\x00")  # ESC M 0 : Font A
        p._raw(b"Font A raw 50:\n")
        p._raw(b"12345678901234567890123456789012345678901234567890\n")
        p._raw(b"\x1bM\x01")  # ESC M 1 : Font B
        p._raw(b"Font B raw 60:\n")
        p._raw(b"123456789012345678901234567890123456789012345678901234567890\n")
        p._raw(b"\n\n\n")


if __name__ == "__main__":
    main()
