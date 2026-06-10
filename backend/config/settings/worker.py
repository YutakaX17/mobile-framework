from __future__ import annotations

from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured


WORKER_BACKENDS = {"sync", "redis"}


def _positive_int(env: Mapping[str, str], key: str, default: str) -> int:
    raw_value = env.get(key, default)
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{key} must be an integer.") from exc
    if value < 1:
        raise ImproperlyConfigured(f"{key} must be greater than zero.")
    return value


def _queues(env: Mapping[str, str]) -> list[str]:
    raw_value = env.get("WORKER_QUEUES", "default")
    queues = [queue.strip() for queue in raw_value.split(",") if queue.strip()]
    if not queues:
        raise ImproperlyConfigured("WORKER_QUEUES must define at least one queue.")
    return queues


def build_worker_config(*, env: Mapping[str, str]) -> dict:
    backend = env.get("WORKER_BACKEND", "sync").strip().lower()
    if backend not in WORKER_BACKENDS:
        raise ImproperlyConfigured(f"WORKER_BACKEND must be one of: {', '.join(sorted(WORKER_BACKENDS))}.")
    return {
        "BACKEND": backend,
        "BROKER_URL": env.get("WORKER_BROKER_URL", "redis://localhost:6379/0"),
        "QUEUES": _queues(env),
        "CONCURRENCY": _positive_int(env, "WORKER_CONCURRENCY", "1"),
        "POLL_INTERVAL_SECONDS": _positive_int(env, "WORKER_POLL_INTERVAL_SECONDS", "5"),
    }
