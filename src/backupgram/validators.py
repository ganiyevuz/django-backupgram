from __future__ import annotations

from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_base_url(value: str) -> None:
    """Accept http(s)://host[:port][/path], including single-label hosts
    (e.g. Docker service names like 'backup'). Rejects other schemes and
    URLs without a host."""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("base_url must start with http:// or https://")
    if not parsed.hostname:
        raise ValidationError("base_url must include a host")
