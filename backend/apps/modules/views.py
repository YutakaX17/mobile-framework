from __future__ import annotations

from django.http import HttpRequest, JsonResponse

from apps.core.api import method_not_allowed, require_tenant_context
from apps.core.errors import ApiError, ApiErrorCode, api_error_response

from .models import ModuleRegistration
from .services import CURRENT_PLATFORM_VERSION, validate_module_compatibility


def _compatibility_status(module: ModuleRegistration) -> dict:
    try:
        validate_module_compatibility(module)
        return {
            "is_compatible": True,
            "platform_version": CURRENT_PLATFORM_VERSION,
            "message": "Compatible with the current platform version.",
        }
    except Exception as exc:
        return {
            "is_compatible": False,
            "platform_version": CURRENT_PLATFORM_VERSION,
            "message": str(exc),
        }


def _serialize_module(module: ModuleRegistration, include_manifest: bool = False) -> dict:
    data = {
        "module_id": module.module_id,
        "name": module.name,
        "version": module.version,
        "schema_version": module.schema_version,
        "plugin_api_version": module.plugin_api_version,
        "platform_min_version": module.platform_min_version,
        "platform_max_version": module.platform_max_version,
        "status": module.status,
        "runtime_min_version": module.manifest.get("runtime_min_version"),
        "runtime_max_version": module.manifest.get("runtime_max_version"),
        "compatibility": _compatibility_status(module),
        "surfaces": module.manifest.get("surfaces", {}),
        "permissions": module.manifest.get("permissions", []),
        "templates": module.manifest.get("extensions", {}).get("templates", {}),
    }
    if include_manifest:
        data["manifest"] = module.manifest
    return data


def module_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.app.manage")
    if isinstance(context, JsonResponse):
        return context

    modules = ModuleRegistration.objects.order_by("module_id", "version")
    return JsonResponse({"modules": [_serialize_module(module) for module in modules]})


def module_detail(request: HttpRequest, module_id: str) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.app.manage")
    if isinstance(context, JsonResponse):
        return context

    module = ModuleRegistration.objects.filter(module_id=module_id).order_by("-version", "-id").first()
    if module is None:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Module `{module_id}` was not found.",
                status_code=404,
            )
        )

    return JsonResponse({"module": _serialize_module(module, include_manifest=True)})
