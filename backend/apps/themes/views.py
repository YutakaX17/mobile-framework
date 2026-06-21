from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse

from apps.core.api import method_not_allowed, require_tenant_context, validation_error_response
from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response

from .models import Theme, ThemeRevision
from .services import create_theme_draft_revision, publish_theme_revision, rollback_theme_revision


def _json_payload_from_request(request: HttpRequest) -> dict | JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return validation_error_response("Request body must be valid JSON.")

    if not isinstance(payload, dict):
        return validation_error_response("Request body must be a JSON object.")

    return payload


def _serialize_revision(revision: ThemeRevision | None, include_payload: bool = False) -> dict | None:
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


def _serialize_current_revision(theme: Theme, include_payload: bool = False) -> dict | None:
    return _serialize_revision(theme.current_revision, include_payload=include_payload)


def _serialize_theme_summary(theme: Theme) -> dict:
    return {
        "description": theme.description,
        "name": theme.name,
        "theme_id": theme.theme_id,
        "current_revision": _serialize_current_revision(theme),
    }


def theme_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.theme.manage")
    if isinstance(context, JsonResponse):
        return context

    themes = (
        Theme.objects.select_related("current_revision")
        .filter(tenant=context.tenant)
        .order_by("theme_id")
    )
    return JsonResponse({"themes": [_serialize_theme_summary(theme) for theme in themes]})


def theme_detail(request: HttpRequest, theme_id: str) -> JsonResponse:
    if request.method not in {"GET", "PUT"}:
        return method_not_allowed("GET or PUT")

    context = require_tenant_context(request, permission="builder.theme.manage")
    if isinstance(context, JsonResponse):
        return context

    try:
        theme = Theme.objects.select_related("current_revision").get(tenant=context.tenant, theme_id=theme_id)
    except Theme.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Theme `{theme_id}` was not found.",
                status_code=404,
            )
        )

    if request.method == "PUT":
        payload = _json_payload_from_request(request)
        if isinstance(payload, JsonResponse):
            return payload

        user = getattr(request, "user", None)
        created_by = user if getattr(user, "is_authenticated", False) else None
        try:
            draft_revision = create_theme_draft_revision(theme, payload, created_by=created_by)
        except ValidationError as exc:
            return validation_error_response("Theme payload is invalid.", exc)

        theme.refresh_from_db()
        data = _serialize_theme_summary(theme)
        data["current_revision"] = _serialize_current_revision(theme, include_payload=True)
        return JsonResponse({
            "draft_revision": _serialize_revision(draft_revision, include_payload=True),
            "theme": data,
        })

    data = _serialize_theme_summary(theme)
    data["current_revision"] = _serialize_current_revision(theme, include_payload=True)
    return JsonResponse({"theme": data})


def theme_revision_publish(request: HttpRequest, theme_id: str, revision: int) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    context = require_tenant_context(request, permission="builder.package.publish")
    if isinstance(context, JsonResponse):
        return context

    try:
        theme = Theme.objects.select_related("current_revision").get(tenant=context.tenant, theme_id=theme_id)
    except Theme.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Theme `{theme_id}` was not found.",
                status_code=404,
            )
        )

    try:
        revision_obj = theme.revisions.get(revision=revision)
    except ThemeRevision.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Theme revision `{revision}` was not found.",
                status_code=404,
            )
        )

    publish_theme_revision(theme, revision_obj)
    theme.refresh_from_db()
    data = _serialize_theme_summary(theme)
    data["current_revision"] = _serialize_current_revision(theme, include_payload=True)
    return JsonResponse({"theme": data})


def theme_revision_rollback(request: HttpRequest, theme_id: str, revision: int) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    context = require_tenant_context(request, permission="builder.package.publish")
    if isinstance(context, JsonResponse):
        return context

    try:
        theme = Theme.objects.select_related("current_revision").get(tenant=context.tenant, theme_id=theme_id)
    except Theme.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Theme `{theme_id}` was not found.",
                status_code=404,
            )
        )

    try:
        revision_obj = theme.revisions.get(revision=revision)
    except ThemeRevision.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Theme revision `{revision}` was not found.",
                status_code=404,
            )
        )

    rollback_theme_revision(theme, revision_obj)
    theme.refresh_from_db()
    data = _serialize_theme_summary(theme)
    data["current_revision"] = _serialize_current_revision(theme, include_payload=True)
    return JsonResponse({"theme": data})
