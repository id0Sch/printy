"""Send a smoke-test receipt to the thermal printer."""

from datetime import datetime

from .printer import open_printer


def main() -> None:
    with open_printer() as p:
        p.set(align="center", bold=True, double_height=True, double_width=True)
        p.text("printy\n")
        p.set(align="center", bold=False, double_height=False, double_width=False)
        p.text("hello, thermal world\n")
        p.text(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        p.text("-" * 32 + "\n")

        p.set(align="left")
        p.text("Plain text line.\n")
        p.set(bold=True)
        p.text("Bold text line.\n")
        p.set(bold=False, underline=1)
        p.text("Underlined line.\n")
        p.set(underline=0)
        p.text("-" * 32 + "\n")

        p.set(align="center")
        p.qr("https://github.com/id0sch/printy", size=6)
        p.text("scan me\n\n")

        p.cut()


if __name__ == "__main__":
    main()
