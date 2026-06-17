from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response
from apps.tenants.models import Tenant

from .models import AppDefinition, AppRevision
from .services import publish_app_revision


def _method_not_allowed(allowed_method: str) -> JsonResponse:
    return api_error_response(
        ApiError(
            code=ApiErrorCode.VALIDATION_ERROR,
            message=f"Only {allowed_method} requests are supported.",
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


def _screen_count(revision: AppRevision | None) -> int:
    if revision is None:
        return 0
    screens = revision.payload.get("screens", [])
    return len(screens) if isinstance(screens, list) else 0


def _navigation_count(revision: AppRevision | None) -> int:
    if revision is None:
        return 0
    navigation = revision.payload.get("navigation", [])
    return len(navigation) if isinstance(navigation, list) else 0


def _permission_count(revision: AppRevision | None) -> int:
    if revision is None:
        return 0
    permissions = revision.payload.get("permissions", [])
    return len(permissions) if isinstance(permissions, list) else 0


def _serialize_revision(revision: AppRevision | None, include_payload: bool = False) -> dict | None:
    if revision is None:
        return None

    data = {
        "navigation_count": _navigation_count(revision),
        "permission_count": _permission_count(revision),
        "revision": revision.revision,
        "schema_version": revision.schema_version,
        "screen_count": _screen_count(revision),
        "status": revision.status,
        "version": revision.version,
    }
    if include_payload:
        data["payload"] = revision.payload
    return data


def _serialize_app_summary(app: AppDefinition) -> dict:
    return {
        "app_id": app.app_id,
        "current_revision": _serialize_revision(app.current_revision),
        "description": app.description,
        "name": app.name,
    }


def app_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    apps = (
        AppDefinition.objects.select_related("current_revision")
        .filter(tenant=tenant)
        .order_by("app_id")
    )
    return JsonResponse({"apps": [_serialize_app_summary(app) for app in apps]})


def app_detail(request: HttpRequest, app_id: str) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    try:
        app = AppDefinition.objects.select_related("current_revision").get(tenant=tenant, app_id=app_id)
    except AppDefinition.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"App `{app_id}` was not found.",
                status_code=404,
            )
        )

    data = _serialize_app_summary(app)
    data["current_revision"] = _serialize_revision(app.current_revision, include_payload=True)
    return JsonResponse({"app": data})


def app_revision_publish(request: HttpRequest, app_id: str, revision: int) -> JsonResponse:
    if request.method != "POST":
        return _method_not_allowed("POST")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    try:
        app = AppDefinition.objects.select_related("current_revision").get(tenant=tenant, app_id=app_id)
    except AppDefinition.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"App `{app_id}` was not found.",
                status_code=404,
            )
        )

    try:
        revision_obj = app.revisions.get(revision=revision)
    except AppRevision.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"App revision `{revision}` was not found.",
                status_code=404,
            )
        )

    publish_app_revision(app, revision_obj)
    app.refresh_from_db()
    data = _serialize_app_summary(app)
    data["current_revision"] = _serialize_revision(app.current_revision, include_payload=True)
    return JsonResponse({"app": data})
