"""Production-like settings driven by environment variables."""

import os

from .database import build_postgres_database_config
from .base import *  # noqa: F403


SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

DATABASES = {
    "default": build_postgres_database_config(env=os.environ, required=True),
}
