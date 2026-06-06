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
    def trigger_backup(self):
        return {"job_id": "job1"}

    def restore(self, **kw):
        FakeClient.restore_kwargs = kw
        return {"job_id": "job2"}

    def list_jobs(self):
        return [{"id": "job1", "type": "backup", "state": "succeeded"}]

    def get_job(self, job_id):
        return {
            "id": job_id,
            "type": "backup",
            "state": "succeeded",
            "exit_code": 0,
            "log_tail": ["done"],
        }

    def list_backups(self):
        return [{"slot": "last", "name": "a.sql.gz"}]


def _patch():
    return patch(
        "backupgram.admin.BackupgramClient.from_server",
        side_effect=lambda s, **k: FakeClient(),
    )


def test_trigger_backup_redirects_to_job(admin_client, srv):
    with _patch():
        resp = admin_client.post(reverse("admin:backupgram_backup", args=[srv.pk]))
    assert resp.status_code == 302
    assert reverse("admin:backupgram_job_detail", args=[srv.pk, "job1"]) in resp.url


def test_backup_requires_post(admin_client, srv):
    resp = admin_client.get(reverse("admin:backupgram_backup", args=[srv.pk]))
    assert resp.status_code == 405


def test_restore_post_calls_client(admin_client, srv):
    with _patch():
        resp = admin_client.post(
            reverse("admin:backupgram_restore", args=[srv.pk]),
            {"file": "last/a.sql.gz", "target_db": "mydb_r", "confirm": "on"},
        )
    assert resp.status_code == 302
    assert FakeClient.restore_kwargs["file"] == "last/a.sql.gz"
    assert FakeClient.restore_kwargs["target_db"] == "mydb_r"


def test_restore_requires_confirm(admin_client, srv):
    with _patch():
        resp = admin_client.post(
            reverse("admin:backupgram_restore", args=[srv.pk]),
            {"file": "last/a.sql.gz", "target_db": "mydb_r"},
        )
    assert resp.status_code == 200  # re-render with form error
    assert b"confirm" in resp.content.lower()


def test_restore_rejects_both_sources(admin_client, srv):
    with _patch():
        resp = admin_client.post(
            reverse("admin:backupgram_restore", args=[srv.pk]),
            {
                "file": "last/a.sql.gz",
                "telegram_message_id": "5",
                "target_db": "d",
                "confirm": "on",
            },
        )
    assert resp.status_code == 200  # form invalid, re-render


def test_restore_rejects_neither_source(admin_client, srv):
    with _patch():
        resp = admin_client.post(
            reverse("admin:backupgram_restore", args=[srv.pk]),
            {"target_db": "d", "confirm": "on"},
        )
    assert resp.status_code == 200  # form invalid (no source), re-render


def test_jobs_and_detail(admin_client, srv):
    with _patch():
        jobs = admin_client.get(reverse("admin:backupgram_jobs", args=[srv.pk]))
        detail = admin_client.get(
            reverse("admin:backupgram_job_detail", args=[srv.pk, "job1"])
        )
    assert jobs.status_code == 200 and b"job1" in jobs.content
    assert detail.status_code == 200 and b"succeeded" in detail.content


def test_job_detail_json_returns_job(admin_client, srv):
    with _patch():
        resp = admin_client.get(
            reverse("admin:backupgram_job_detail_json", args=[srv.pk, "job1"])
        )
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/json"
    import json

    data = json.loads(resp.content)
    assert data["id"] == "job1" and data["state"] == "succeeded"
