"""Local development settings."""

import os

from .database import build_postgres_database_config
from .base import *  # noqa: F403


DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

if os.environ.get("DJANGO_DATABASE_ENGINE", "").lower() in {"postgres", "postgresql"}:
    DATABASES = {
        "default": build_postgres_database_config(env=os.environ, required=False),
    }
