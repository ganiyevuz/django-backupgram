from __future__ import annotations

import contextlib
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import ModelAdmin, register
from django.http import HttpResponseNotAllowed, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from backupgram.client import BackupgramAPIError, BackupgramClient
from backupgram.forms import BackupServerForm, RestoreForm
from backupgram.models import BackupServer


@register(BackupServer)
class BackupServerAdmin(ModelAdmin):
    form = BackupServerForm
    list_display = ["name", "base_url", "enabled", "reachable_badge", "manage_link"]
    readonly_fields = ["created_at", "updated_at", "manage_link"]

    @staticmethod
    def _client(server):
        timeout = getattr(settings, "BACKUPGRAM_REACHABILITY_TIMEOUT", 3)
        return BackupgramClient(
            server.base_url, server.token, verify=server.verify_tls, timeout=timeout
        )

    def manage_link(self, obj):
        if obj is None or obj.pk is None:
            return "Save first, then manage backups from the changelist."
        url = reverse("admin:backupgram_dashboard", args=[obj.pk])
        return format_html('<a class="button" href="{}">Open dashboard →</a>', url)

    manage_link.short_description = "manage"

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
            path(
                "<uuid:pk>/backup/",
                av(self.backup_view),
                name="backupgram_backup",
            ),
            path(
                "<uuid:pk>/restore/",
                av(self.restore_view),
                name="backupgram_restore",
            ),
            path(
                "<uuid:pk>/jobs/",
                av(self.jobs_view),
                name="backupgram_jobs",
            ),
            path(
                "<uuid:pk>/jobs/<job_id>/",
                av(self.job_detail_view),
                name="backupgram_job_detail",
            ),
            path(
                "<uuid:pk>/config/",
                av(self.config_view),
                name="backupgram_config",
            ),
            path(
                "<uuid:pk>/config/<key>/reset/",
                av(self.config_reset_view),
                name="backupgram_config_reset",
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

    def backup_view(self, request, pk):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        server = get_object_or_404(BackupServer, pk=pk)
        try:
            job = BackupgramClient.from_server(server).trigger_backup()
            messages.success(request, "Backup triggered.")
            return redirect(
                reverse("admin:backupgram_job_detail", args=[server.pk, job["job_id"]])
            )
        except BackupgramAPIError as exc:
            messages.error(request, f"Backup failed: {exc}")
            return redirect(reverse("admin:backupgram_dashboard", args=[server.pk]))

    def restore_view(self, request, pk):
        server = get_object_or_404(BackupServer, pk=pk)
        if request.method == "POST":
            form = RestoreForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                try:
                    job = BackupgramClient.from_server(server).restore(
                        file=cd.get("file") or None,
                        telegram_message_id=cd.get("telegram_message_id") or None,
                        target_db=cd["target_db"],
                        confirm=True,
                    )
                    messages.success(request, "Restore started.")
                    return redirect(
                        reverse(
                            "admin:backupgram_job_detail",
                            args=[server.pk, job["job_id"]],
                        )
                    )
                except BackupgramAPIError as exc:
                    messages.error(request, f"Restore failed: {exc}")
        else:
            form = RestoreForm(initial={"file": request.GET.get("file", "")})
        backups = []
        with contextlib.suppress(BackupgramAPIError):
            backups = BackupgramClient.from_server(server).list_backups()
        return render(
            request,
            "backupgram/admin/restore.html",
            self._ctx(request, server, form=form, backups=backups),
        )

    def jobs_view(self, request, pk):
        server = get_object_or_404(BackupServer, pk=pk)
        jobs, error = [], None
        try:
            jobs = BackupgramClient.from_server(server).list_jobs()
        except BackupgramAPIError as exc:
            error = str(exc)
        return render(
            request,
            "backupgram/admin/jobs.html",
            self._ctx(request, server, jobs=jobs, error=error),
        )

    def job_detail_view(self, request, pk, job_id):
        server = get_object_or_404(BackupServer, pk=pk)
        job, error = None, None
        try:
            job = BackupgramClient.from_server(server).get_job(job_id)
        except BackupgramAPIError as exc:
            error = str(exc)
        running = bool(job and job.get("state") in ("queued", "running"))
        return render(
            request,
            "backupgram/admin/job_detail.html",
            self._ctx(request, server, job=job, error=error, running=running),
        )

    def config_view(self, request, pk):
        server = get_object_or_404(BackupServer, pk=pk)
        client = BackupgramClient.from_server(server)
        if request.method == "POST":
            try:
                current = client.get_config()
            except BackupgramAPIError as exc:
                messages.error(request, f"Could not load config: {exc}")
                return redirect(reverse("admin:backupgram_config", args=[server.pk]))
            patch = {}
            for key, meta in current.items():
                submitted = request.POST.get(key, "")
                is_secret = "set" in meta  # secret entries expose {set:bool}, not value
                if is_secret:
                    if submitted:  # only send a secret if a new value was typed
                        patch[key] = submitted
                elif submitted != meta.get("value", ""):
                    patch[key] = submitted
            if patch:
                try:
                    client.patch_config(patch)
                    messages.success(request, f"Updated {', '.join(sorted(patch))}.")
                except BackupgramAPIError as exc:
                    messages.error(request, f"Update failed: {exc}")
            else:
                messages.info(request, "No changes.")
            return redirect(reverse("admin:backupgram_config", args=[server.pk]))
        config, error = {}, None
        try:
            config = client.get_config()
        except BackupgramAPIError as exc:
            error = str(exc)
        items = []
        for key in sorted(config):
            meta = config[key]
            items.append(
                {
                    "key": key,
                    "secret": "set" in meta,
                    "value": meta.get("value", ""),
                    "is_set": meta.get("set", False),
                    "source": meta.get("source", ""),
                }
            )
        return render(
            request,
            "backupgram/admin/config.html",
            self._ctx(request, server, items=items, error=error),
        )

    def config_reset_view(self, request, pk, key):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        server = get_object_or_404(BackupServer, pk=pk)
        try:
            BackupgramClient.from_server(server).delete_config(key)
            messages.success(request, f"Reset {key} to base.")
        except BackupgramAPIError as exc:
            messages.error(request, f"Reset failed: {exc}")
        return redirect(reverse("admin:backupgram_config", args=[server.pk]))
