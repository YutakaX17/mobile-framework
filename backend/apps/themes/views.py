from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response
from apps.tenants.models import Tenant

from .models import Theme


def _method_not_allowed() -> JsonResponse:
    return api_error_response(
        ApiError(
            code=ApiErrorCode.VALIDATION_ERROR,
            message="Only GET requests are supported.",
            status_code=405,
        )
    )


def _tenant_from_request(request: HttpRequest) -> Tenant | JsonResponse:
    tenant_slug = request.GET.get("tenant", "").strip()
    if not tenant_slug:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.VALIDATION_ERROR,
                message="A tenant query parameter is required.",
                details=[ApiErrorDetail(field="tenant", message="Provide a tenant slug.")],
                status_code=400,
            )
        )
    try:
        return Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Tenant `{tenant_slug}` was not found.",
                status_code=404,
            )
        )


def _serialize_current_revision(theme: Theme, include_payload: bool = False) -> dict | None:
    revision = theme.current_revision
    if revision is None:
        return None

    data = {
        "revision": revision.revision,
        "schema_version": revision.schema_version,
        "status": revision.status,
        "version": revision.version,
    }
    if include_payload:
        data["payload"] = revision.payload
    return data


def _serialize_theme_summary(theme: Theme) -> dict:
    return {
        "description": theme.description,
        "name": theme.name,
        "theme_id": theme.theme_id,
        "current_revision": _serialize_current_revision(theme),
    }


def theme_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed()

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    themes = (
        Theme.objects.select_related("current_revision")
        .filter(tenant=tenant)
        .order_by("theme_id")
    )
    return JsonResponse({"themes": [_serialize_theme_summary(theme) for theme in themes]})


def theme_detail(request: HttpRequest, theme_id: str) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed()

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    try:
        theme = Theme.objects.select_related("current_revision").get(tenant=tenant, theme_id=theme_id)
    except Theme.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Theme `{theme_id}` was not found.",
                status_code=404,
            )
        )

    data = _serialize_theme_summary(theme)
    data["current_revision"] = _serialize_current_revision(theme, include_payload=True)
    return JsonResponse({"theme": data})
