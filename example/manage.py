#!/usr/bin/env python
"""Django management entrypoint for the django-backupgram example project.

Run from the repo root or from example/:
    uv run python example/manage.py migrate
    uv run python example/manage.py runserver
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # When invoked as `python example/manage.py`, Python puts example/ on sys.path
    # automatically; make it explicit so `uv run` / reloader subprocesses agree.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
