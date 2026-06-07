# django-backupgram

A Django admin control panel for the [postgres-backup REST API](https://github.com/ganiyevuz/docker-postgres-backup-telegram).

## What it is

`django-backupgram` is a thin Django admin client. It talks to one or more
[postgres-backup-telegram](https://github.com/ganiyevuz/docker-postgres-backup-telegram)
containers over their REST API, letting you:

- **Trigger backups** on demand
- **Browse and download** backup files
- **Delete** old backups
- **Restore** a backup to a target database
- **Watch async jobs** (restore, backup) as they run
- **Edit runtime config** of the backup container

It does **not** perform backups itself — the backup logic lives entirely inside
the containers. `django-backupgram` is only the admin UI that drives them.

## Requirements

- Python 3.11 – 3.13
- Django 5.2+
- One or more backup containers reachable from the Django server with
  `REST_API_ENABLE=TRUE` and a `REST_API_TOKEN` set

See the backup container's
[REST API docs](https://github.com/ganiyevuz/docker-postgres-backup-telegram/blob/main/docs/REST_API.md)
for how to enable the API.

## Install

```bash
pip install django-backupgram
```

## Setup

1. Add `"backupgram"` to `INSTALLED_APPS`:

   ```python
   INSTALLED_APPS = [
       ...
       "backupgram",
   ]
   ```

2. Run migrations:

   ```bash
   python manage.py migrate
   ```

3. Open Django admin → **Backup servers** → **Add**, and fill in:
   - **Name** — a friendly label (e.g. `production`)
   - **Base URL** — the backup container's REST API endpoint, e.g.
     `https://backup:8081`. Docker service names are allowed (the request is
     made server-side).
   - **Token** — the bearer token configured via `REST_API_TOKEN` on the container
     (see below).

### The API token

The token is the backup container's single admin bearer key — you generate it
yourself and set it on the container, then paste the **same** value into the
**Token** field here.

Generate a high-entropy value (≥ 32 bytes of randomness):

```bash
openssl rand -base64 48
# or
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set it on the backup container via `REST_API_TOKEN` (or, recommended,
`REST_API_TOKEN_FILE` pointing at a Docker secret), then enter the same token in
admin. The container compares it in constant time and refuses to start if the API
is enabled without one; here it is stored **encrypted at rest** and sent only
server-side. To **rotate**: change it on the container, recreate it, and update
the Token field. See the
[REST API auth docs](https://github.com/ganiyevuz/docker-postgres-backup-telegram/blob/main/docs/REST_API.md#authentication).

## Usage

From the **Backup servers** changelist, each server row shows a reachability
badge and links to its dashboard. The dashboard provides:

| Action | Notes |
|--------|-------|
| **Run backup** | Triggers an immediate backup |
| **Backups** | Lists all backup files; download or delete individual files |
| **Restore** | Select a file, enter the target database name, confirm |
| **Jobs** | Live view of async jobs (backup/restore in progress) |
| **Config** | View and edit the container's runtime configuration |

Long-running operations (restore, triggered backup) run as async jobs inside
the backup container. Refresh the Jobs page to see progress and final status.

## Security

- The bearer token is stored **encrypted at rest** using Fernet symmetric
  encryption. The key is derived from Django's `SECRET_KEY`.
- The token is **write-only** in the admin interface — it is never rendered back
  into any form or page.
- **Rotating `SECRET_KEY` invalidates all stored tokens.** After a key rotation,
  re-enter each server's token in the admin.
- All REST calls are made **server-side** — the token never reaches the browser.
- Put the backup container's REST API behind **TLS and a reverse proxy**. Do not
  expose it directly on a public network.

## Optional settings

Add to your Django settings to override defaults:

```python
# Timeout (seconds) for the reachability check shown in the changelist badge.
# Default: 3
BACKUPGRAM_REACHABILITY_TIMEOUT = 3
```

## Development

```bash
uv sync
uv run pytest
```

## Links

- Backup container: <https://github.com/ganiyevuz/docker-postgres-backup-telegram>
- REST API reference: <https://github.com/ganiyevuz/docker-postgres-backup-telegram/blob/main/docs/REST_API.md>
- This package: <https://github.com/ganiyevuz/django-backupgram>
