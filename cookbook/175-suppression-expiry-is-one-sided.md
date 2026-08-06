# 175 — A guessed suppression expiry only self-heals in one direction

**Tags:** snooze, mute, suppress, silence, alert fatigue, known issue, expiry, TTL, allowlist, exclusion list, monitoring, health check, flaky test skip, self-healing, stale suppression, one-sided failure

**Extracted from:** KinoBerlin (2026-08-06)

## The problem

Something is legitimately quiet — a venue on summer break, a vendor API down for maintenance, a test
that can't pass until an upstream fix lands. You suppress the alert so it stops crying wolf, and
because you know unbounded suppression rots, you do the responsible thing and give it an **expiry**:

```python
SUMMER_PAUSE_UNTIL = {
    "il-kino":        "2026-08-13",   # published resume date — exact
    "xenon-kino":     "2026-09-01",   # no published date — a GUESS
    "cineplex-adria": "2026-09-01",   # ditto
}
```

This feels safe. It even has a comment explaining that a lapsed entry re-flags by itself, so nothing
can stay silenced forever. **That reasoning is only half true.**

The expiry protects you when the thing stays broken:

```
still dark at the expiry  ->  entry lapses  ->  check re-flags  ->  you look.   SELF-HEALS
```

It does nothing when the thing **recovers early**:

```
comes back before the expiry  ->  nothing re-checks  ->  still suppressed  ->  silence.   ROTS
```

You now have a *working* component excluded from monitoring, and the exclusion persists until a date
you invented. In the real case both guessed entries had resumed weeks early and would have stayed
unmonitored until 1 September — a 3½-week hole in exactly the check meant to catch their failure.

## Why you will not notice

A suppressed check emits nothing whether the subject is healthy or broken. That is the whole point of
suppression, and it is why this failure is invisible: **the silence you asked for and the silence of a
missed outage are the same silence.** Nothing in the system distinguishes "quiet because suppressed"
from "quiet because fine" — you only find out by going and looking, which is the thing you suppressed
the alert to avoid doing.

## The fix: key suppression on the observation, not only the clock

The date should be a **backstop**, not the mechanism. Drop the entry the moment the subject shows
signs of life:

```python
def active_suppressions(subject_has_data, today):
    """A suppression survives only while BOTH hold: it hasn't expired, AND the
    subject is still actually quiet. Recovery clears it without human action."""
    live = set()
    for subject, until in SUPPRESS_UNTIL.items():
        if today >= date.fromisoformat(until):
            continue                      # lapsed  -> re-flag (the old, one-sided guard)
        if subject_has_data(subject):
            log.info("%s produced data again — suppression cleared early", subject)
            continue                      # recovered -> re-flag (the missing half)
        live.add(subject)
    return live
```

Two properties worth keeping:

- **Log the early clear.** A suppression that silently deletes itself is its own small mystery later.
- **Keep the dated dict, not a permanent set.** The date still catches "never came back". You want
  both guards; they cover opposite failures.

If auto-clearing is too clever for your case, the cheap version is a rule: **re-verify every guessed
entry whenever you touch the file** — not only when one lapses. Write that in the comment, because
the next reader will otherwise trust the expiry exactly as far as you did.

## Distinguish exact expiries from guesses

`il-kino` above had a *published* resume date; the other two were invented. Same syntax, completely
different confidence. Mark it — a guess deserves the recovery check, a published date mostly doesn't:

```python
"xenon-kino": ("2026-09-01", GUESS),   # revisit on touch
"il-kino":    ("2026-08-13", PUBLISHED),
```

## Generalizes to

Any list whose entries mean "don't tell me about this for now": muted monitors and PagerDuty
maintenance windows, `@pytest.mark.skip(reason="upstream bug")`, lint/type-checker ignore
directives, `# noqa` with a ticket, feature flags left off "temporarily", known-failure allowlists
in CI, deprecation warnings filtered. All of them rot the same way, and all of them rot **quietly**.

Same family as the "nothing prunes this" trap: a list that is only ever *added to* grows dead
entries. This is its sibling — a list that only ever expires *late*.
