from __future__ import annotations

from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured


POSTGRES_DEFAULTS = {
    "POSTGRES_DB": "mobile_framework",
    "POSTGRES_USER": "mobile_framework",
    "POSTGRES_PASSWORD": "mobile_framework",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_CONN_MAX_AGE": "60",
}


def _env_value(env: Mapping[str, str], key: str, *, required: bool) -> str:
    value = env.get(key)
    if value:
        return value
    if required:
        raise ImproperlyConfigured(f"{key} is required for PostgreSQL database settings.")
    return POSTGRES_DEFAULTS[key]


def _connection_max_age(env: Mapping[str, str]) -> int:
    raw_value = env.get("POSTGRES_CONN_MAX_AGE", POSTGRES_DEFAULTS["POSTGRES_CONN_MAX_AGE"])
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ImproperlyConfigured("POSTGRES_CONN_MAX_AGE must be an integer.") from exc


def build_postgres_database_config(*, env: Mapping[str, str], required: bool) -> dict:
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env_value(env, "POSTGRES_DB", required=required),
        "USER": _env_value(env, "POSTGRES_USER", required=required),
        "PASSWORD": _env_value(env, "POSTGRES_PASSWORD", required=required),
        "HOST": _env_value(env, "POSTGRES_HOST", required=False),
        "PORT": _env_value(env, "POSTGRES_PORT", required=False),
        "CONN_MAX_AGE": _connection_max_age(env),
    }
    sslmode = env.get("POSTGRES_SSLMODE", "").strip()
    if sslmode:
        config["OPTIONS"] = {"sslmode": sslmode}
    return config
