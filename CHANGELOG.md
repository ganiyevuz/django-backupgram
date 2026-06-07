# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-06-07

### Removed

- **`django-jazzmin` dependency.** It was never used by the package — every admin
  view extends Django's built-in `admin/base_site.html` — so it no longer forces
  installs to pull in jazzmin or adopt that admin theme. Add any admin theme you
  like in your own project. (Also dropped from the bundled `example/` settings.)

## [0.1.0] - 2026-06-07

Initial release — a Django admin control panel for the `backupgram`
(postgres-backup) REST API. It is a thin, well-tested client: it performs no
backups itself, it drives one or more backup containers over their REST API.

### Added

- **`BackupServer` model** — register one or more backup servers (`base_url`,
  bearer `token`, `verify_tls`, `timeout`, `enabled`). The token is **encrypted
  at rest** with Fernet (key derived from `SECRET_KEY`) and is **write-only** in
  admin (never rendered). `base_url` accepts single-label hosts, e.g.
  `https://backup:8081` (Docker service names).
- **`BackupgramClient`** — typed `httpx` wrapper over every REST endpoint
  (status, list/download/delete backups, trigger backup, restore from a stored
  file or a Telegram message id, jobs, runtime config) with a `BackupgramAPIError`
  that carries the HTTP status and parses the API's `{"error": ...}` envelope.
- **Admin dashboard** — server overview with a live connection indicator, KPI
  cards (schedule with a human-readable cron description, last backup, next
  backup), a status & configuration card grid (upload mode, Telegram / MTProto
  state, cluster, previous backup), misconfiguration **warnings** (e.g. upload
  method `mtproto` without API credentials), and a recent-backups panel.
- **Backups page** — list, stream-download, and delete (with confirmation),
  human-readable sizes and relative times.
- **Jobs** — recent-jobs list and a live job-detail view that auto-refreshes
  while a job is running.
- **Restore page** — restore from a stored file or a Telegram message id;
  clicking an available backup fills the file field. Server-side `target_db`
  validation and explicit confirmation are required.
- **Runtime config** — settings grouped into sections (Schedule / Retention /
  Databases / Telegram / Webhook), each rendered with the right widget: enum
  **selects** with per-value help (including `TELEGRAM_UPLOAD_METHOD`), numbers,
  write-only secrets, and a **live cron editor** (bundled cronstrue, MIT) with
  preset shortcuts. Only whitelisted keys are editable; secrets are masked.
- **Next-run calculation** — computed in pure standard library (no external
  cron dependency), supporting 5-field cron and `@shortcut` schedules.
- **Theming** — a data-dense dashboard UI that follows Django admin's light/dark
  theme; CSS and JS are bundled and shipped in the wheel.
- **Packaging** — `src/` layout, Python 3.11–3.13 / Django 5.2+, PyPI
  trusted-publishing release workflow, and an `example/` project for local
  testing against a running backup container.

### Security

- Server tokens are encrypted at rest and never returned to the browser; all
  REST calls happen server-side. Admin views are permission-gated, destructive
  actions are POST + CSRF + explicit confirm, and config secrets are masked
  (write-only). **Note:** rotating `SECRET_KEY` invalidates stored tokens.

[Unreleased]: https://github.com/ganiyevuz/django-backupgram/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/ganiyevuz/django-backupgram/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ganiyevuz/django-backupgram/releases/tag/v0.1.0
