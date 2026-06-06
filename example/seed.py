"""Idempotently seed the example project:

- a superuser  admin / admin
- a BackupServer 'local' pointing at the backup container's REST API

Run:  uv run python example/seed.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

from backupgram.models import BackupServer  # noqa: E402

# Connection to the locally-running backup container (docker-compose.local.yml
# publishes the REST API on 127.0.0.1:8081 with token "devsecret").
BASE_URL = os.environ.get("BACKUPGRAM_DEMO_URL", "http://localhost:8081")
TOKEN = os.environ.get("BACKUPGRAM_DEMO_TOKEN", "devsecret")

User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin")
    print("✅ created superuser  admin / admin")
else:
    print("ℹ️  superuser 'admin' already exists")

server, created = BackupServer.objects.get_or_create(
    name="local",
    defaults={"base_url": BASE_URL, "token": TOKEN, "verify_tls": False},
)
if not created:
    server.base_url = BASE_URL
    server.token = TOKEN
    server.verify_tls = False
    server.save()
verb = "✅ created" if created else "ℹ️  updated"
print(f"{verb} BackupServer 'local' → {server.base_url}")
print("\nNext:  uv run python example/manage.py runserver")
print("       http://localhost:8000/admin/   (admin / admin)")
