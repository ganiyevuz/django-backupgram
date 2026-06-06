import time

from backupgram.templatetags.bg_extras import ago, dur


def test_ago_buckets():
    now = int(time.time())
    assert ago(now).endswith("s ago")
    assert ago(now - 120) == "2m ago"
    assert ago(now - 7200) == "2h ago"
    assert ago(now - 172800) == "2d ago"
    assert ago(None) == ""


def test_dur_buckets():
    assert dur(30) == "30s"
    assert dur(120) == "2m"
    assert dur(7200) == "2h"
    assert dur(172800) == "2d"
    assert dur(None) == ""
