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
