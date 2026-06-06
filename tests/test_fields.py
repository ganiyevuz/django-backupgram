from django.db.models import Model

from backupgram.fields import EncryptedTextField


class _Holder(Model):
    secret = EncryptedTextField(blank=True, default="")

    class Meta:
        app_label = "backupgram"


def test_roundtrip_via_prep_and_from_db():
    f = EncryptedTextField()
    stored = f.get_prep_value("hunter2")
    assert stored != "hunter2"  # ciphertext at rest
    assert f.from_db_value(stored, None, None) == "hunter2"


def test_empty_is_passthrough():
    f = EncryptedTextField()
    assert f.get_prep_value("") == ""
    assert f.from_db_value("", None, None) == ""


def test_none_is_passthrough():
    f = EncryptedTextField()
    assert f.get_prep_value(None) is None
    assert f.from_db_value(None, None, None) is None


def test_undecryptable_returns_empty():
    f = EncryptedTextField()
    assert f.from_db_value("not-a-valid-token", None, None) == ""
