Format this as a printy receipt for an alert. Use these fields when calling print_message:

- sender: the source system (e.g. "Datadog", "PostHog", "monitor")
- subject: "{title}" (bold, centered, ≤32 chars — shorten if needed)
- body: format like this (one [SEVERITY] line, blank line, then details):

[{severity_upper}]

{body}

Then call print_message(sender=..., subject=..., body=<the above>).
