from __future__ import annotations

from datetime import datetime

from croniter import croniter

# go-cron / Quartz @shortcuts → standard 5-field cron (croniter parses 5-field).
_SHORTCUTS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


def next_run(schedule: str, base: datetime) -> datetime | None:
    """Next fire time at/after `base` for a cron expression or @shortcut.
    Returns None for unsupported/invalid expressions (e.g. '@every ...')."""
    if not schedule:
        return None
    expr = _SHORTCUTS.get(schedule.strip(), schedule.strip())
    if expr.startswith("@"):
        return None  # @every and unknown shortcuts: not computed
    try:
        if not croniter.is_valid(expr):
            return None
        return croniter(expr, base).get_next(datetime)
    except (ValueError, KeyError):
        return None
