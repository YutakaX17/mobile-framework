#!/usr/bin/env python
"""Django command-line utility for the backend control plane."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not installed. Install backend dependencies before running manage.py."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
