from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse

from apps.identity.models import UserRoleAssignment
from apps.tenants.models import Tenant

from .errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response


TENANT_HEADER = "X-Tenant-Slug"


@dataclass(frozen=True)
class TenantContext:
    tenant: Tenant
    source: str


def method_not_allowed(allowed_method: str) -> JsonResponse:
    return api_error_response(
        ApiError(
            code=ApiErrorCode.VALIDATION_ERROR,
            message=f"Only {allowed_method} requests are supported.",
            status_code=405,
        )
    )


def json_payload_from_request(request: HttpRequest) -> dict[str, Any] | JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (JSONDecodeError, UnicodeDecodeError):
        return api_error_response(
            ApiError(
                code=ApiErrorCode.VALIDATION_ERROR,
                message="Request body must be valid JSON.",
                details=[ApiErrorDetail(field="body", message="Provide a valid JSON object.")],
                status_code=400,
            )
        )
    if not isinstance(payload, dict):
        return api_error_response(
            ApiError(
                code=ApiErrorCode.VALIDATION_ERROR,
                message="Request body must be a JSON object.",
                details=[ApiErrorDetail(field="body", message="Provide a JSON object.")],
                status_code=400,
            )
        )
    return payload


def required_query_param(request: HttpRequest, name: str) -> str | JsonResponse:
    value = request.GET.get(name, "").strip()
    if value:
        return value
    return api_error_response(
        ApiError(
            code=ApiErrorCode.VALIDATION_ERROR,
            message=f"A {name} query parameter is required.",
            details=[ApiErrorDetail(field=name, message=f"Provide a {name} value.")],
            status_code=400,
        )
    )


def validation_error_response(message: str, error: ValidationError | None = None) -> JsonResponse:
    details: list[ApiErrorDetail] = []
    if error is not None:
        if hasattr(error, "message_dict"):
            for field, messages in error.message_dict.items():
                details.extend(ApiErrorDetail(field=field, message=str(item)) for item in messages)
        else:
            details.extend(ApiErrorDetail(message=str(item)) for item in error.messages)

    return api_error_response(
        ApiError(
            code=ApiErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=400,
        )
    )


def tenant_slug_from_request(request: HttpRequest) -> tuple[str, str] | None:
    header_value = request.headers.get(TENANT_HEADER, "").strip()
    if header_value:
        return header_value, "header"

    query_value = request.GET.get("tenant", "").strip()
    if query_value:
        return query_value, "query"

    return None


def resolve_tenant_from_request(request: HttpRequest) -> TenantContext | JsonResponse:
    tenant_slug = tenant_slug_from_request(request)
    if tenant_slug is None:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.VALIDATION_ERROR,
                message=f"A {TENANT_HEADER} header is required.",
                details=[
                    ApiErrorDetail(
                        field=TENANT_HEADER,
                        message="Provide a tenant slug. The ?tenant=slug query parameter remains temporary dev compatibility.",
                    )
                ],
                status_code=400,
            )
        )

    slug, source = tenant_slug
    try:
        return TenantContext(tenant=Tenant.objects.get(slug=slug), source=source)
    except Tenant.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Tenant `{slug}` was not found.",
                status_code=404,
            )
        )


def user_tenant_assignments(user, tenant: Tenant | None = None):
    assignments = UserRoleAssignment.objects.select_related("tenant", "role").filter(user=user, is_active=True)
    if tenant is not None:
        assignments = assignments.filter(tenant=tenant)
    return assignments


def user_tenant_permissions(user, tenant: Tenant) -> set[str]:
    if not getattr(user, "is_authenticated", False):
        return set()
    assignments = user_tenant_assignments(user, tenant).prefetch_related("role__permissions")
    permissions: set[str] = set()
    for assignment in assignments:
        permissions.update(assignment.role.permissions.values_list("code", flat=True))
    return permissions


def user_has_tenant_access(user, tenant: Tenant) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return user_tenant_assignments(user, tenant).exists()


def user_has_tenant_permission(user, tenant: Tenant, permission_code: str) -> bool:
    return permission_code in user_tenant_permissions(user, tenant)


def authentication_required_response() -> JsonResponse:
    return api_error_response(
        ApiError(
            code=ApiErrorCode.AUTHENTICATION_REQUIRED,
            message="Authentication is required.",
            status_code=401,
        )
    )


def permission_denied_response(message: str = "Permission denied.") -> JsonResponse:
    return api_error_response(
        ApiError(
            code=ApiErrorCode.PERMISSION_DENIED,
            message=message,
            status_code=403,
        )
    )


def require_tenant_context(
    request: HttpRequest,
    *,
    permission: str | None = None,
) -> TenantContext | JsonResponse:
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return authentication_required_response()

    context = resolve_tenant_from_request(request)
    if isinstance(context, JsonResponse):
        return context

    if not user_has_tenant_access(user, context.tenant):
        return permission_denied_response(f"User does not have access to tenant `{context.tenant.slug}`.")

    if permission and not user_has_tenant_permission(user, context.tenant, permission):
        return permission_denied_response(f"User is missing required permission `{permission}`.")

    return context
