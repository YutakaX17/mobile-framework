"""Local development settings."""

import os

from .database import build_postgres_database_config
from .base import *  # noqa: F403


DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

if os.environ.get("DJANGO_DATABASE_ENGINE", "").lower() in {"postgres", "postgresql"}:
    DATABASES = {
        "default": build_postgres_database_config(env=os.environ, required=False),
    }
