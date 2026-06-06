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
    def get_config(self):
        return {
            "SCHEDULE": {"value": "@daily", "source": "base"},
            "TELEGRAM_BOT_TOKEN": {"set": False, "source": "base"},
        }

    def patch_config(self, mapping):
        FakeClient.patched = mapping
        return {"config": {}}

    def delete_config(self, key):
        FakeClient.deleted = key
        return {"cleared": key}


def _patch():
    return patch(
        "backupgram.admin.BackupgramClient.from_server",
        side_effect=lambda s, **k: FakeClient(),
    )


def test_config_renders(admin_client, srv):
    with _patch():
        resp = admin_client.get(reverse("admin:backupgram_config", args=[srv.pk]))
    assert resp.status_code == 200
    assert b"SCHEDULE" in resp.content


def test_config_patch_sends_only_changed_nonblank(admin_client, srv):
    with _patch():
        admin_client.post(
            reverse("admin:backupgram_config", args=[srv.pk]),
            {"SCHEDULE": "@hourly", "TELEGRAM_BOT_TOKEN": ""},
        )
    assert FakeClient.patched == {
        "SCHEDULE": "@hourly"
    }  # changed non-secret sent; blank secret omitted


def test_config_patch_includes_typed_secret(admin_client, srv):
    with _patch():
        admin_client.post(
            reverse("admin:backupgram_config", args=[srv.pk]),
            {"SCHEDULE": "@daily", "TELEGRAM_BOT_TOKEN": "newtok"},
        )
    assert FakeClient.patched == {
        "TELEGRAM_BOT_TOKEN": "newtok"
    }  # unchanged SCHEDULE omitted, typed secret sent


def test_config_reset_key(admin_client, srv):
    with _patch():
        resp = admin_client.post(
            reverse("admin:backupgram_config_reset", args=[srv.pk, "SCHEDULE"])
        )
    assert resp.status_code == 302
    assert FakeClient.deleted == "SCHEDULE"


def test_config_reset_requires_post(admin_client, srv):
    resp = admin_client.get(
        reverse("admin:backupgram_config_reset", args=[srv.pk, "SCHEDULE"])
    )
    assert resp.status_code == 405


def test_config_get_handles_api_error(admin_client, srv):
    from backupgram.client import BackupgramAPIError

    class Boom:
        def get_config(self):
            raise BackupgramAPIError("server down", status=502)

    with patch(
        "backupgram.admin.BackupgramClient.from_server",
        side_effect=lambda s, **k: Boom(),
    ):
        resp = admin_client.get(reverse("admin:backupgram_config", args=[srv.pk]))
    assert resp.status_code == 200
    assert b"server down" in resp.content
