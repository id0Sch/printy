Format this calendar day as a printy receipt.

Layout rules:
- Subject: short date like "{date}" (≤32 chars)
- All-day events first, prefixed with "all-day:" header and "- " bullets
- Then a separator line of 32 dashes
- Then timed events, one per line: "HH:MM  Event name"
  - HH:MM is 5 chars, two spaces, then event (≤25 chars; truncate if longer)
  - Mark declined events with "(decl.)" suffix
  - Mark OOO/personal time with "(OOO)" suffix
- Keep every line ≤32 chars

Events to format:
{events}

Then call print_message(sender="calendar", subject="{date}", body=<formatted>).
