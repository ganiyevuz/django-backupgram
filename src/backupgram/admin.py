from __future__ import annotations

from django.conf import settings
from django.contrib.admin import ModelAdmin, register
from django.utils.html import format_html

from backupgram.client import BackupgramClient
from backupgram.forms import BackupServerForm
from backupgram.models import BackupServer


@register(BackupServer)
class BackupServerAdmin(ModelAdmin):
    form = BackupServerForm
    list_display = ["name", "base_url", "enabled", "reachable_badge"]
    readonly_fields = ["created_at", "updated_at"]

    @staticmethod
    def _client(server):
        timeout = getattr(settings, "BACKUPGRAM_REACHABILITY_TIMEOUT", 3)
        return BackupgramClient(
            server.base_url, server.token, verify=server.verify_tls, timeout=timeout
        )

    def reachable_badge(self, obj):
        try:
            ok = self._client(obj).reachable()
        except Exception:
            ok = False
        color, label = (
            ("#1a7f37", "● reachable") if ok else ("#cf222e", "● unreachable")
        )
        return format_html('<span style="color:{}">{}</span>', color, label)

    reachable_badge.short_description = "status"
