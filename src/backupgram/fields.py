from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db.models import TextField


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    # Derive a stable 32-byte key from SECRET_KEY.
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


class EncryptedTextField(TextField):
    """A TextField that encrypts its value at rest with Fernet (key derived from
    SECRET_KEY). NOTE: rotating SECRET_KEY invalidates previously-stored values —
    they decrypt to "" and must be re-entered."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == "":
            return value
        return _fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except (InvalidToken, ValueError):
            return ""
