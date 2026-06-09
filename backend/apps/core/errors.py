from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from django.core.exceptions import ValidationError
from django.http import JsonResponse


class ApiErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_REQUIRED = "authentication_required"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_error"


def _normalize_code(code: ApiErrorCode | str) -> str:
    return code.value if isinstance(code, ApiErrorCode) else code


@dataclass(frozen=True)
class ApiErrorDetail:
    message: str
    code: ApiErrorCode | str = ApiErrorCode.VALIDATION_ERROR
    field: str = ""

    def __post_init__(self) -> None:
        code = _normalize_code(self.code)
        errors = {}
        if not code:
            errors["code"] = "API error detail code is required."
        if not self.message:
            errors["message"] = "API error detail message is required."
        if errors:
            raise ValidationError(errors)
        object.__setattr__(self, "code", code)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "code": self.code,
            "message": self.message,
        }
        if self.field:
            data["field"] = self.field
        return data


@dataclass(frozen=True)
class ApiError:
    code: ApiErrorCode | str
    message: str
    status_code: int = 400
    details: list[ApiErrorDetail] = field(default_factory=list)
    request_id: str = ""
    correlation_id: str = ""

    def __post_init__(self) -> None:
        code = _normalize_code(self.code)
        errors = {}
        if not code:
            errors["code"] = "API error code is required."
        if not self.message:
            errors["message"] = "API error message is required."
        if not isinstance(self.status_code, int) or not 400 <= self.status_code <= 599:
            errors["status_code"] = "API error status code must be an HTTP 4xx or 5xx status."
        if not isinstance(self.details, list) or any(not isinstance(detail, ApiErrorDetail) for detail in self.details):
            errors["details"] = "API error details must be a list of ApiErrorDetail objects."
        if errors:
            raise ValidationError(errors)
        object.__setattr__(self, "code", code)

    def to_dict(self) -> dict[str, Any]:
        error = {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "details": [detail.to_dict() for detail in self.details],
        }
        if self.request_id:
            error["request_id"] = self.request_id
        if self.correlation_id:
            error["correlation_id"] = self.correlation_id
        return {"error": error}


def api_error_response(error: ApiError) -> JsonResponse:
    return JsonResponse(error.to_dict(), status=error.status_code)
