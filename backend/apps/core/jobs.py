from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from django.core.exceptions import ValidationError


JobHandler = Callable[["BackgroundJob"], Any]


class BackgroundJobStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class BackgroundJob:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    queue: str = "default"
    request_id: str = ""
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        errors = {}
        if not self.name:
            errors["name"] = "Background job name is required."
        if not self.queue:
            errors["queue"] = "Background job queue is required."
        if not isinstance(self.payload, dict):
            errors["payload"] = "Background job payload must be a dictionary."
        if not isinstance(self.metadata, dict):
            errors["metadata"] = "Background job metadata must be a dictionary."
        if errors:
            raise ValidationError(errors)


@dataclass(frozen=True)
class BackgroundJobResult:
    job: BackgroundJob
    status: BackgroundJobStatus | str
    value: Any = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        status = self.status.value if isinstance(self.status, BackgroundJobStatus) else self.status
        errors = {}
        if status not in {choice.value for choice in BackgroundJobStatus}:
            errors["status"] = "Background job result status is invalid."
        if not isinstance(self.metadata, dict):
            errors["metadata"] = "Background job result metadata must be a dictionary."
        if errors:
            raise ValidationError(errors)
        object.__setattr__(self, "status", status)


class BackgroundJobRegistry:
    def __init__(self):
        self._handlers: dict[str, JobHandler] = {}

    def register(self, job_name: str, handler: JobHandler) -> None:
        if not job_name:
            raise ValidationError({"job_name": "Background job name is required."})
        if not callable(handler):
            raise ValidationError({"handler": "Background job handler must be callable."})
        self._handlers[job_name] = handler

    def unregister(self, job_name: str) -> None:
        self._handlers.pop(job_name, None)

    def run(self, job: BackgroundJob) -> BackgroundJobResult:
        handler = self._handlers.get(job.name)
        if handler is None:
            raise ValidationError({"job": f"No background job handler registered for `{job.name}`."})
        try:
            value = handler(job)
        except Exception as exc:  # noqa: BLE001 - worker boundary should return failure results.
            return BackgroundJobResult(job=job, status=BackgroundJobStatus.FAILED, error=str(exc))
        return BackgroundJobResult(job=job, status=BackgroundJobStatus.SUCCEEDED, value=value)

    def reset(self) -> None:
        self._handlers.clear()


default_job_registry = BackgroundJobRegistry()
