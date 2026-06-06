from __future__ import annotations

from uuid import uuid4

from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    Model,
    PositiveIntegerField,
    URLField,
    UUIDField,
)

from backupgram.fields import EncryptedTextField


class BackupServer(Model):
    id = UUIDField(primary_key=True, default=uuid4, editable=False)
    name = CharField(max_length=100, unique=True)
    base_url = URLField(help_text="REST API base, e.g. https://host:8081")
    token = EncryptedTextField(help_text="Admin bearer token (stored encrypted).")
    verify_tls = BooleanField(default=True)
    timeout = PositiveIntegerField(default=30, help_text="Request timeout (seconds).")
    enabled = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
