from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.core.api import (
    authentication_required_response,
    json_payload_from_request,
    method_not_allowed,
    require_tenant_context,
    user_tenant_assignments,
    user_tenant_permissions,
)
from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response
from apps.identity.models import UserRoleAssignment


def _serialize_user(user) -> dict:
    return {
        "display_name": user.get_full_name() or user.get_username(),
        "email": user.email,
        "id": user.id,
        "is_staff": user.is_staff,
        "username": user.get_username(),
    }


def _serialize_tenant_assignment(assignment: UserRoleAssignment) -> dict:
    permissions = sorted(assignment.role.permissions.values_list("code", flat=True))
    return {
        "permissions": permissions,
        "role": {
            "name": assignment.role.name,
            "slug": assignment.role.slug,
        },
        "tenant": {
            "id": str(assignment.tenant.id),
            "name": assignment.tenant.name,
            "slug": assignment.tenant.slug,
            "status": assignment.tenant.status,
        },
    }


@ensure_csrf_cookie
def csrf_token(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")
    return JsonResponse({"csrf_token": get_token(request)})


def login_view(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    payload = json_payload_from_request(request)
    if isinstance(payload, JsonResponse):
        return payload

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if not username or not password:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.VALIDATION_ERROR,
                message="Username and password are required.",
                details=[
                    ApiErrorDetail(field="username", message="Provide a username."),
                    ApiErrorDetail(field="password", message="Provide a password."),
                ],
                status_code=400,
            )
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.AUTHENTICATION_REQUIRED,
                message="Invalid username or password.",
                status_code=401,
            )
        )

    login(request, user)
    return JsonResponse({"user": _serialize_user(user)})


def logout_view(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")
    logout(request)
    return JsonResponse({"status": "ok"})


@ensure_csrf_cookie
def current_session(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return authentication_required_response()
    return JsonResponse({"user": _serialize_user(user)})


def tenant_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return authentication_required_response()

    assignments = user_tenant_assignments(user).prefetch_related("role__permissions").order_by(
        "tenant__slug",
        "role__slug",
    )
    return JsonResponse({"tenants": [_serialize_tenant_assignment(assignment) for assignment in assignments]})


def current_tenant(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request)
    if isinstance(context, JsonResponse):
        return context

    return JsonResponse(
        {
            "tenant": {
                "id": str(context.tenant.id),
                "name": context.tenant.name,
                "slug": context.tenant.slug,
                "status": context.tenant.status,
            },
            "permissions": sorted(user_tenant_permissions(request.user, context.tenant)),
            "source": context.source,
        }
    )
