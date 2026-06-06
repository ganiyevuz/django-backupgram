from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from backupgram.models import BackupServer

pytestmark = pytest.mark.django_db


@pytest.fixture
def srv():
    return BackupServer.objects.create(
        name="prod", base_url="https://backup.example.com:8081", token="t"
    )


@pytest.fixture
def admin_client(client):
    User = get_user_model()
    User.objects.create_superuser("boss", "b@x.io", "pw")
    client.login(username="boss", password="pw")
    return client


class FakeClient:
    def status(self):
        return {
            "schedule": "@daily",
            "cluster": False,
            "last_backup": {"status": "OK", "age_seconds": 60},
        }

    def list_backups(self):
        return [{"slot": "last", "name": "a.sql.gz", "size": 10, "mtime": 1}]

    def delete_backup(self, slot, name):
        FakeClient.deleted = (slot, name)
        return {"deleted": name}

    def iter_backup(self, slot, name, chunk_size=1):
        yield b"DUMP"

    def get_config(self):
        return {
            "TELEGRAM_UPLOAD_METHOD": {"value": "smart", "source": "base"},
            "TELEGRAM_CHAT_ID": {"value": "123", "source": "base"},
            "TELEGRAM_BOT_TOKEN": {"set": True, "source": "base"},
            "TELEGRAM_API_ID": {"set": False, "source": "base"},
            "TELEGRAM_API_HASH": {"set": False, "source": "base"},
        }


def _patch():
    return patch(
        "backupgram.admin.BackupgramClient.from_server",
        side_effect=lambda s, **k: FakeClient(),
    )


def test_dashboard(admin_client, srv):
    with _patch():
        resp = admin_client.get(reverse("admin:backupgram_dashboard", args=[srv.pk]))
    assert resp.status_code == 200
    assert b"@daily" in resp.content
    assert b"Status &amp; configuration" in resp.content
    assert b"Upload mode" in resp.content
    assert b"Next backup" in resp.content
    assert b"Previous backup" in resp.content


def test_backups_list(admin_client, srv):
    with _patch():
        resp = admin_client.get(reverse("admin:backupgram_backups", args=[srv.pk]))
    assert resp.status_code == 200
    assert b"a.sql.gz" in resp.content


def test_download_streams(admin_client, srv):
    with _patch():
        resp = admin_client.get(
            reverse("admin:backupgram_download", args=[srv.pk, "last", "a.sql.gz"])
        )
    assert resp.status_code == 200
    assert b"".join(resp.streaming_content) == b"DUMP"
    assert "a.sql.gz" in resp["Content-Disposition"]


def test_backups_list_handles_api_error(admin_client, srv):
    from backupgram.client import BackupgramAPIError

    class Boom:
        def list_backups(self):
            raise BackupgramAPIError("server down", status=502)

    with patch(
        "backupgram.admin.BackupgramClient.from_server",
        side_effect=lambda s, **k: Boom(),
    ):
        resp = admin_client.get(reverse("admin:backupgram_backups", args=[srv.pk]))
    assert resp.status_code == 200
    assert b"server down" in resp.content


def test_delete_requires_post(admin_client, srv):
    url = reverse("admin:backupgram_delete_backup", args=[srv.pk, "last", "a.sql.gz"])
    with _patch():
        get = admin_client.get(url)
        assert get.status_code == 405
        post = admin_client.post(url)
        assert post.status_code == 302
    assert FakeClient.deleted == ("last", "a.sql.gz")
