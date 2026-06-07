# Example project

A minimal, local-only Django project for manually exercising `django-backupgram`
against a running backup container. **Not** shipped in the published wheel.

## Prerequisites

A reachable backup container with the REST API enabled. The companion repo's
`docker-compose.local.yml` publishes it on `127.0.0.1:8081` with token `devsecret`:

```sh
# in the backupgram repo:
docker compose -f docker-compose.local.yml up -d
```

## Run

From the `django-backupgram` repo root:

```sh
uv run python example/manage.py migrate      # create the SQLite db
uv run python example/seed.py                # superuser admin/admin + a 'local' BackupServer
uv run python example/manage.py runserver    # http://localhost:8000/admin/
```

Log in as `admin` / `admin`, open **Backup servers → local**, and use the
dashboard: Run backup, browse/download/restore backups, watch jobs, edit config.

Override the target via env if your container is elsewhere:

```sh
BACKUPGRAM_DEMO_URL=http://localhost:8081 BACKUPGRAM_DEMO_TOKEN=devsecret uv run python example/seed.py
```
