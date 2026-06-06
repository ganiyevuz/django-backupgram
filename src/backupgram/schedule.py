"""Compute the next fire time of a cron schedule — pure stdlib, no deps.

Supports standard 5-field cron (minute hour day-of-month month day-of-week)
with `*`, lists (`a,b`), ranges (`a-b`), and steps (`*/n`, `a-b/n`), plus the
common `@shortcut` names. Returns None for anything it can't compute
(e.g. `@every ...`, malformed expressions)."""

from __future__ import annotations

from datetime import datetime, timedelta

# go-cron / Quartz @shortcuts → standard 5-field cron.
_SHORTCUTS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# search horizon: a cron that never matches (e.g. Feb 30) gives up after this.
_MAX_DAYS = 366


def _parse_field(spec: str, lo: int, hi: int) -> set[int]:
    """Parse one cron field into the set of allowed integers (raises on garbage)."""
    values: set[int] = set()
    for part in spec.split(","):
        step = 1
        rng = part
        if "/" in part:
            rng, step_s = part.split("/", 1)
            step = int(step_s)
            if step <= 0:
                raise ValueError("step must be positive")
        if rng == "*":
            start, end = lo, hi
        elif "-" in rng:
            a, b = rng.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(rng)
        if start < lo or end > hi or start > end:
            raise ValueError("field out of range")
        if start == end:
            values.add(start)
        else:
            values.update(range(start, end + 1, step))
    return values


def _first_of_next_month(t: datetime) -> datetime:
    year, month = (t.year + 1, 1) if t.month == 12 else (t.year, t.month + 1)
    return t.replace(
        year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
    )


def next_run(schedule: str, base: datetime) -> datetime | None:
    if not schedule:
        return None
    expr = _SHORTCUTS.get(schedule.strip(), schedule.strip())
    if expr.startswith("@"):
        return None  # @every and unknown shortcuts: not computed
    fields = expr.split()
    if len(fields) != 5:
        return None
    try:
        minutes = _parse_field(fields[0], 0, 59)
        hours = _parse_field(fields[1], 0, 23)
        doms = _parse_field(fields[2], 1, 31)
        months = _parse_field(fields[3], 1, 12)
        dows = {d % 7 for d in _parse_field(fields[4], 0, 7)}  # 0 and 7 = Sunday
    except (ValueError, IndexError):
        return None

    dom_restricted = fields[2] != "*"
    dow_restricted = fields[4] != "*"

    def day_matches(t: datetime) -> bool:
        dom_ok = t.day in doms
        cron_dow = (t.weekday() + 1) % 7  # Python Mon=0..Sun=6 → cron Sun=0..Sat=6
        dow_ok = cron_dow in dows
        if dom_restricted and dow_restricted:
            return dom_ok or dow_ok
        if dom_restricted:
            return dom_ok
        if dow_restricted:
            return dow_ok
        return True

    t = base.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = t + timedelta(days=_MAX_DAYS)
    while t < limit:
        if t.month not in months:
            t = _first_of_next_month(t)
            continue
        if not day_matches(t):
            t = (t + timedelta(days=1)).replace(hour=0, minute=0)
            continue
        if t.hour not in hours:
            t = (t + timedelta(hours=1)).replace(minute=0)
            continue
        if t.minute not in minutes:
            t += timedelta(minutes=1)
            continue
        return t
    return None
