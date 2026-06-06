"""UI metadata for known runtime-config keys: widget kind, help text, and enum
choices. Keys not listed fall back to a plain text input."""

from __future__ import annotations

# kind: "text" | "number" | "select" | "cron"   (secrets are detected separately)
CONFIG_FIELD_META: dict[str, dict] = {
    "SCHEDULE": {
        "kind": "cron",
        "help": (
            "Cron expression (5 fields) or an @shortcut."
            " A live description appears as you type."
        ),
    },
    "TELEGRAM_NOTIFY_ON": {
        "kind": "select",
        "help": "When to send Telegram notifications.",
        "choices": [
            ("all", "all — notify on every run"),
            ("success", "success — only when a backup succeeds"),
            ("failure", "failure — only when a backup fails"),
        ],
    },
    "TELEGRAM_UPLOAD_METHOD": {
        "kind": "select",
        "help": "How backups are delivered to Telegram.",
        "choices": [
            ("smart", "smart — Bot API under 50 MB, MTProto above (recommended)"),
            ("botapi", "botapi — Bot API only (max 50 MB per file)"),
            ("mtproto", "mtproto — MTProto only, up to 2 GB (needs API ID & hash)"),
        ],
    },
    "POSTGRES_DB_AUTODISCOVER": {
        "kind": "select",
        "help": "Back up every non-template database found on the server.",
        "choices": [
            ("TRUE", "TRUE — discover all databases"),
            ("FALSE", "FALSE — only the configured POSTGRES_DB"),
        ],
    },
    "BACKUP_KEEP_MINS": {
        "kind": "number",
        "help": "Retain the latest backups for this many minutes.",
    },
    "BACKUP_KEEP_DAYS": {
        "kind": "number",
        "help": "Days of daily backups to keep.",
    },
    "BACKUP_KEEP_WEEKS": {
        "kind": "number",
        "help": "Weeks of weekly backups to keep.",
    },
    "BACKUP_KEEP_MONTHS": {
        "kind": "number",
        "help": "Months of monthly backups to keep.",
    },
    "BACKUP_MIN_DISK_SPACE": {
        "kind": "number",
        "help": "Abort if free space (MB) is below this.",
    },
    "BACKUP_MAX_AGE_HOURS": {
        "kind": "number",
        "help": "Healthcheck fails if the last backup is older than this many hours.",
    },
    "POSTGRES_DB": {
        "kind": "text",
        "help": "Comma-separated database name(s).",
    },
    "POSTGRES_DB_EXCLUDE": {
        "kind": "text",
        "help": "Comma-separated databases to skip in auto-discover.",
    },
    "POSTGRES_EXTRA_OPTS": {
        "kind": "text",
        "help": "Extra pg_dump flags, e.g. -Z9 -Fc.",
    },
    "POSTGRES_EXCLUDE_TABLES": {
        "kind": "text",
        "help": "Comma-separated tables to exclude.",
    },
    "TELEGRAM_CHAT_ID": {
        "kind": "text",
        "help": "Chat id(s), comma-separated for multiple destinations.",
    },
    "TELEGRAM_THREAD_ID": {
        "kind": "text",
        "help": "Forum topic id (optional).",
    },
    "TELEGRAM_API_URL": {
        "kind": "text",
        "help": "Custom Bot API base URL (optional).",
    },
    "WEBHOOK_EXTRA_ARGS": {
        "kind": "text",
        "help": "Extra curl args passed to the webhook.",
    },
}
