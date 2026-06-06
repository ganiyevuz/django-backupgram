from __future__ import annotations

from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import ModelAdmin, register
from django.http import HttpResponseNotAllowed, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from backupgram.client import BackupgramAPIError, BackupgramClient
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

    def get_urls(self):
        av = self.admin_site.admin_view
        mine = [
            path(
                "<uuid:pk>/dashboard/",
                av(self.dashboard_view),
                name="backupgram_dashboard",
            ),
            path(
                "<uuid:pk>/backups/",
                av(self.backups_view),
                name="backupgram_backups",
            ),
            path(
                "<uuid:pk>/backups/<slot>/<name>/download/",
                av(self.download_view),
                name="backupgram_download",
            ),
            path(
                "<uuid:pk>/backups/<slot>/<name>/delete/",
                av(self.delete_backup_view),
                name="backupgram_delete_backup",
            ),
        ]
        return mine + super().get_urls()

    def _ctx(self, request, server, **extra):
        ctx = {
            **self.admin_site.each_context(request),
            "server": server,
            "opts": self.model._meta,
        }
        ctx.update(extra)
        return ctx

    def dashboard_view(self, request, pk):
        server = get_object_or_404(BackupServer, pk=pk)
        status, error = None, None
        try:
            status = BackupgramClient.from_server(server).status()
        except BackupgramAPIError as exc:
            error = str(exc)
        return render(
            request,
            "backupgram/admin/dashboard.html",
            self._ctx(request, server, status=status, error=error),
        )

    def backups_view(self, request, pk):
        server = get_object_or_404(BackupServer, pk=pk)
        backups, error = [], None
        try:
            backups = BackupgramClient.from_server(server).list_backups()
        except BackupgramAPIError as exc:
            error = str(exc)
        return render(
            request,
            "backupgram/admin/backups.html",
            self._ctx(request, server, backups=backups, error=error),
        )

    def download_view(self, request, pk, slot, name):
        server = get_object_or_404(BackupServer, pk=pk)
        gen = BackupgramClient.from_server(server).iter_backup(slot, name)
        try:
            first = next(gen)
        except StopIteration:
            first = b""
        except BackupgramAPIError as exc:
            messages.error(request, f"Download failed: {exc}")
            return redirect(reverse("admin:backupgram_backups", args=[server.pk]))

        def stream():
            yield first
            yield from gen

        safe_name = name.replace('"', "")
        resp = StreamingHttpResponse(stream(), content_type="application/octet-stream")
        resp["Content-Disposition"] = (
            f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{quote(name)}"
        )
        return resp

    def delete_backup_view(self, request, pk, slot, name):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        server = get_object_or_404(BackupServer, pk=pk)
        try:
            BackupgramClient.from_server(server).delete_backup(slot, name)
            messages.success(request, f"Deleted {name}.")
        except BackupgramAPIError as exc:
            messages.error(request, f"Delete failed: {exc}")
        return redirect(reverse("admin:backupgram_backups", args=[server.pk]))
