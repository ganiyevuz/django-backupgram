from datetime import UTC, datetime

from backupgram.schedule import next_run


def test_next_run_daily_shortcut():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    nxt = next_run("@daily", base)
    assert nxt is not None and nxt.hour == 0 and nxt.day == 2


def test_next_run_cron():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    nxt = next_run("0 3 * * *", base)
    assert nxt is not None and nxt.hour == 3


def test_next_run_unsupported():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert next_run("@every 5m", base) is None
    assert next_run("", base) is None
    assert next_run("garbage", base) is None
    assert next_run("0 3 * *", base) is None  # only 4 fields
    assert next_run("99 3 * * *", base) is None  # minute out of range


def test_next_run_step_and_list():
    base = datetime(2026, 1, 1, 12, 5, tzinfo=UTC)
    nxt = next_run("*/15 * * * *", base)  # every 15 min → 12:15
    assert nxt is not None and nxt.hour == 12 and nxt.minute == 15
    nxt = next_run("0 9,17 * * *", base)  # 09:00 / 17:00 → next 17:00
    assert nxt is not None and nxt.hour == 17 and nxt.minute == 0


def test_next_run_day_of_week():
    # 2026-01-01 is a Thursday; "0 0 * * 1" = Mondays → 2026-01-05.
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    nxt = next_run("0 0 * * 1", base)
    assert nxt is not None and nxt.day == 5 and nxt.weekday() == 0


def test_next_run_preserves_tz():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    nxt = next_run("@daily", base)
    assert nxt is not None and nxt.tzinfo is not None
