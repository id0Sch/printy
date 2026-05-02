"""Print rulers in Font A and Font B to determine real line widths."""
from .printer import open_printer


def main() -> None:
    with open_printer() as p:
        p.set(font="a", bold=False, double_width=False, double_height=False)
        p.text("Font A ruler:\n")
        p.text("12345678901234567890123456789012345678901234567890\n")
        p.text("---\n")
        p.set(font="b")
        p.text("Font B ruler:\n")
        p.text("123456789012345678901234567890123456789012345678901234567890\n")
        p.set(font="a")
        p.ln(3)


if __name__ == "__main__":
    main()
