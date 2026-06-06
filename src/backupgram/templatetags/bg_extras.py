from __future__ import annotations

import time

from django.template import Library

register = Library()


@register.filter
def ago(epoch):
    """Render a unix-epoch int as a short relative time, e.g. '5m ago'."""
    try:
        secs = int(time.time()) - int(epoch)
    except (TypeError, ValueError):
        return ""
    if secs < 0:
        secs = 0
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


@register.filter
def dur(seconds):
    """Render a duration in seconds as a compact age, e.g. '2h', '3d'."""
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return ""
    if s < 0:
        s = 0
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"
