import pytest

from backupgram.models import BackupServer

pytestmark = pytest.mark.django_db


def test_token_encrypted_at_rest_but_readable():
    s = BackupServer.objects.create(
        name="prod", base_url="https://h:8081", token="secret-tok"
    )
    again = BackupServer.objects.get(pk=s.pk)
    assert again.token == "secret-tok"  # transparently decrypted
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute(
            "SELECT token FROM backupgram_backupserver WHERE name = %s", ["prod"]
        )
        raw = cur.fetchone()[0]
    assert raw != "secret-tok"  # ciphertext at rest


def test_defaults_and_str():
    s = BackupServer.objects.create(
        name="staging", base_url="https://h:8081", token="t"
    )
    assert s.enabled is True
    assert s.verify_tls is True
    assert s.timeout == 30
    assert str(s) == "staging"
