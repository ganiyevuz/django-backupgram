import json

import httpx
import pytest

from backupgram.client import BackupgramAPIError, BackupgramClient


def _client(handler):
    transport = httpx.MockTransport(handler)
    return BackupgramClient("https://h:8081", "tok", transport=transport)


def test_sends_bearer_and_parses_backups():
    seen = {}

    def handler(req):
        seen["auth"] = req.headers.get("authorization")
        seen["path"] = req.url.path
        return httpx.Response(
            200, json={"backups": [{"slot": "last", "name": "a.sql.gz"}]}
        )

    out = _client(handler).list_backups()
    assert seen["auth"] == "Bearer tok"
    assert seen["path"] == "/backups"
    assert out == [{"slot": "last", "name": "a.sql.gz"}]


def test_error_envelope_becomes_exception():
    def handler(req):
        return httpx.Response(403, json={"error": "config key not allowed: X"})

    with pytest.raises(BackupgramAPIError) as ei:
        _client(handler).patch_config({"X": "y"})
    assert ei.value.status == 403
    assert "not allowed" in str(ei.value)


def test_trigger_backup_returns_job_id():
    def handler(req):
        assert req.method == "POST" and req.url.path == "/backup"
        return httpx.Response(202, json={"job_id": "abc"})

    assert _client(handler).trigger_backup() == {"job_id": "abc"}


def test_restore_requires_exactly_one_source():
    c = _client(lambda req: httpx.Response(202, json={"job_id": "x"}))
    with pytest.raises(BackupgramAPIError):
        c.restore(target_db="d")  # neither source
    with pytest.raises(BackupgramAPIError):
        c.restore(file="last/a", telegram_message_id=5, target_db="d")  # both


def test_restore_file_builds_body():
    sent = {}

    def handler(req):
        sent.update(json.loads(req.content))
        return httpx.Response(202, json={"job_id": "x"})

    _client(handler).restore(file="last/a.sql.gz", target_db="d")
    assert sent == {"target_db": "d", "confirm": True, "file": "last/a.sql.gz"}


def test_restore_telegram_builds_body():
    sent = {}

    def handler(req):
        sent.update(json.loads(req.content))
        return httpx.Response(202, json={"job_id": "x"})

    _client(handler).restore(telegram_message_id=1234, target_db="d")
    assert sent == {"target_db": "d", "confirm": True, "telegram_message_id": 1234}


def test_delete_backup_sends_confirm():
    seen = {}

    def handler(req):
        seen["q"] = dict(req.url.params)
        seen["m"] = req.method
        return httpx.Response(200, json={"deleted": "a.sql.gz"})

    _client(handler).delete_backup("last", "a.sql.gz")
    assert seen["m"] == "DELETE" and seen["q"].get("confirm") == "true"


def test_get_config_unwraps():
    c = _client(
        lambda req: httpx.Response(
            200, json={"config": {"SCHEDULE": {"value": "@daily"}}}
        )
    )
    assert c.get_config() == {"SCHEDULE": {"value": "@daily"}}


def test_get_job_and_list_jobs():
    def handler(req):
        if req.url.path == "/jobs":
            return httpx.Response(200, json={"jobs": [{"id": "j1"}]})
        return httpx.Response(200, json={"id": "j1", "state": "succeeded"})

    c = _client(handler)
    assert c.list_jobs() == [{"id": "j1"}]
    assert c.get_job("j1")["state"] == "succeeded"


def test_iter_backup_streams_bytes():
    def handler(req):
        assert req.url.path == "/backups/last/a.sql.gz"
        return httpx.Response(200, content=b"DUMPDATA")

    chunks = b"".join(_client(handler).iter_backup("last", "a.sql.gz"))
    assert chunks == b"DUMPDATA"


def test_iter_backup_error_raises_with_envelope():
    def handler(req):
        return httpx.Response(404, json={"error": "backup not found"})

    with pytest.raises(BackupgramAPIError) as ei:
        list(_client(handler).iter_backup("last", "missing.sql.gz"))
    assert ei.value.status == 404
    assert "not found" in str(ei.value)


def test_network_error_becomes_apierror():
    def handler(req):
        raise httpx.ConnectError("boom")

    with pytest.raises(BackupgramAPIError):
        _client(handler).status()


def test_reachable_true_false():
    ok = _client(lambda r: httpx.Response(200, json={"status": "ok"}))
    assert ok.reachable() is True
    assert _client(lambda r: httpx.Response(500, text="boom")).reachable() is False
