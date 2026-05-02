PRINTY THERMAL PRINTER SPEC

Hardware: MIAOBAO 58Printer (58mm thermal, USB)
Paper width: 32 chars per line in Font A (used by default)
Auto-cutter: NO — receipts feed 3 blank lines and are torn off by hand

Supported ESC/POS formatting:
- bold, underline, center/left/right alignment
- font A (default, 32 cols), font B (smaller, ~50 cols but ugly)
- QR codes via escpos (used in test_print only)

NOT supported / unreliable:
- double-width text (consumes columns, often wraps mid-letter)
- images / graphics (technically work via escpos but slow over USB)
- cut command (printer ignores it — no auto-cutter)
- right alignment looks awkward on 32 cols, prefer center or left

Formatting rules for body text:
1. The render layer wraps body lines to 32 chars on word boundaries.
   You don't need to pre-wrap, BUT if you want columns to line up
   (e.g. time + event), pre-format with spaces and keep each line ≤32 chars.
2. Use "-" * 32 or "=" * 32 as separators — they're already used
   automatically around the title and at the end.
3. Don't put long unbreakable tokens (URLs, hashes) — they'll get
   chopped mid-character. Truncate or use a QR code instead.
4. Newlines in the body are preserved. Use them to make sections.
5. Subject is auto-centered, bold. Keep ≤32 chars or it wraps.

Stylistic conventions used in this household:
- Calendar prints: time on left (5 chars HH:MM), 2 spaces, then event.
- Alert prints: severity in [BRACKETS] on its own line above the body.
- Restaurant-order prints: ">> SECTION  [tag]" headers, "  - bullet" items.
