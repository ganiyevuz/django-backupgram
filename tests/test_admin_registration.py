import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from backupgram.models import BackupServer

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client):
    User = get_user_model()
    User.objects.create_superuser("boss", "b@x.io", "pw")
    client.login(username="boss", password="pw")
    return client


def test_changelist_renders(admin_client):
    BackupServer.objects.create(
        name="prod", base_url="https://backup.example.com:8081", token="t"
    )
    resp = admin_client.get(reverse("admin:backupgram_backupserver_changelist"))
    assert resp.status_code == 200
    assert b"prod" in resp.content


def test_token_is_write_only_blank_keeps_existing(admin_client):
    s = BackupServer.objects.create(
        name="prod", base_url="https://backup.example.com:8081", token="orig"
    )
    url = reverse("admin:backupgram_backupserver_change", args=[s.pk])
    resp = admin_client.post(
        url,
        {
            "name": "prod",
            "base_url": "https://backup.example.com:8081",
            "token": "",
            "verify_tls": "on",
            "timeout": "30",
            "enabled": "on",
        },
    )
    assert resp.status_code in (302, 200)
    assert BackupServer.objects.get(pk=s.pk).token == "orig"


def test_add_sets_token(admin_client):
    url = reverse("admin:backupgram_backupserver_add")
    admin_client.post(
        url,
        {
            "name": "new",
            "base_url": "https://backup.example.com:8081",
            "token": "fresh",
            "verify_tls": "on",
            "timeout": "30",
            "enabled": "on",
        },
    )
    assert BackupServer.objects.get(name="new").token == "fresh"
