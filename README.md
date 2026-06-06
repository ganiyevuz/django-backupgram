# django-backupgram

A Django admin control panel for the postgres-backup REST API (backupgram).

## Installation

```bash
pip install django-backupgram
```

Add `"backupgram"` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "backupgram",
]
```

## Development

```bash
uv sync
uv run pytest
```
