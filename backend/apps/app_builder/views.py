from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from apps.core.api import method_not_allowed, require_tenant_context
from apps.core.errors import ApiError, ApiErrorCode, api_error_response

from .models import AppDefinition, AppRevision
from .services import publish_app_revision


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
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.app.manage")
    if isinstance(context, JsonResponse):
        return context

    apps = (
        AppDefinition.objects.select_related("current_revision")
        .filter(tenant=context.tenant)
        .order_by("app_id")
    )
    return JsonResponse({"apps": [_serialize_app_summary(app) for app in apps]})


def app_detail(request: HttpRequest, app_id: str) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.app.manage")
    if isinstance(context, JsonResponse):
        return context

    try:
        app = AppDefinition.objects.select_related("current_revision").get(tenant=context.tenant, app_id=app_id)
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
        return method_not_allowed("POST")

    context = require_tenant_context(request, permission="builder.app.manage")
    if isinstance(context, JsonResponse):
        return context

    try:
        app = AppDefinition.objects.select_related("current_revision").get(tenant=context.tenant, app_id=app_id)
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
