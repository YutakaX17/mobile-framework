from __future__ import annotations

from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse

from apps.app_builder.models import AppDefinition, AppRevisionStatus
from apps.core.api import (
    json_payload_from_request,
    method_not_allowed,
    required_query_param,
    require_tenant_context,
    resolve_tenant_from_request,
    validation_error_response,
)
from apps.core.errors import ApiError, ApiErrorCode, api_error_response
from apps.form_builder.models import FormDefinition, FormRevisionStatus
from apps.modules.models import ModuleRegistration, ModuleRegistrationStatus
from apps.tenants.models import Tenant
from apps.themes.models import Theme, ThemeRevisionStatus

from .models import DeploymentPackage, DeploymentPackageStatus
from .services import (
    activate_deployment_package,
    active_deployment_package,
    compile_deployment_package,
    validate_release_channel_name,
)


def _tenant_from_request(request: HttpRequest) -> Tenant | JsonResponse:
    context = resolve_tenant_from_request(request)
    if isinstance(context, JsonResponse):
        return context
    return context.tenant


def _serialize_package_manifest(package: DeploymentPackage) -> dict:
    return {
        "app_id": package.app_id,
        "app_version": package.app_version,
        "channel": package.channel,
        "created_at": package.created_at.isoformat(),
        "hash": package.package_hash,
        "package_id": package.package_id,
        "platform_version": package.platform_version,
        "runtime_max_version": package.runtime_max_version,
        "runtime_min_version": package.runtime_min_version,
        "signature": package.signature,
        "status": package.status,
        "updated_at": package.updated_at.isoformat(),
    }


def _serialize_admin_package(package: DeploymentPackage, include_payload: bool = False) -> dict:
    data = _serialize_package_manifest(package)
    data["signature_status"] = "present" if package.signature else "missing"
    data["runtime_compatibility"] = {
        "min_version": package.runtime_min_version,
        "max_version": package.runtime_max_version,
    }
    data["module_count"] = len(package.payload.get("modules", []))
    data["form_count"] = len(package.payload.get("forms", []))
    if include_payload:
        data["payload"] = package.payload
    return data


def _form_ids_from_app_payload(payload: dict) -> list[str]:
    form_ids: list[str] = []
    for screen in payload.get("screens", []):
        if not isinstance(screen, dict):
            continue
        for component in screen.get("components", []):
            if not isinstance(component, dict):
                continue
            if component.get("component_type") != "form":
                continue
            binding = component.get("binding", {})
            form_id = binding.get("form_id") if isinstance(binding, dict) else None
            if isinstance(form_id, str) and form_id and form_id not in form_ids:
                form_ids.append(form_id)
    return form_ids


def _not_found(message: str) -> JsonResponse:
    return api_error_response(
        ApiError(
            code=ApiErrorCode.NOT_FOUND,
            message=message,
            status_code=404,
        )
    )


def admin_package_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.package.publish")
    if isinstance(context, JsonResponse):
        return context

    packages = DeploymentPackage.objects.filter(tenant=context.tenant).order_by("-updated_at", "-id")
    return JsonResponse({"packages": [_serialize_admin_package(package) for package in packages]})


def admin_package_detail(request: HttpRequest, package_id: str) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    context = require_tenant_context(request, permission="builder.package.publish")
    if isinstance(context, JsonResponse):
        return context

    try:
        package = DeploymentPackage.objects.get(tenant=context.tenant, package_id=package_id)
    except DeploymentPackage.DoesNotExist:
        return _not_found(f"Package `{package_id}` was not found.")

    return JsonResponse({"package": _serialize_admin_package(package, include_payload=True)})


def admin_package_compile(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    context = require_tenant_context(request, permission="builder.package.publish")
    if isinstance(context, JsonResponse):
        return context

    payload = json_payload_from_request(request)
    if isinstance(payload, JsonResponse):
        return payload

    package_id = str(payload.get("package_id", "")).strip()
    app_id = str(payload.get("app_id", "")).strip()
    channel = str(payload.get("channel", "dev")).strip() or "dev"
    runtime_min_version = str(payload.get("runtime_min_version", "0.1.0")).strip()
    runtime_max_version = str(payload.get("runtime_max_version", "0.1.0")).strip()
    platform_version = str(payload.get("platform_version", "0.1.0")).strip()
    signing_key = str(payload.get("signing_key", "")).strip() or None

    if not package_id:
        return validation_error_response("Package payload is invalid.", ValidationError({"package_id": "Required."}))
    if not app_id:
        return validation_error_response("Package payload is invalid.", ValidationError({"app_id": "Required."}))

    try:
        validate_release_channel_name(channel)
    except ValidationError as exc:
        return validation_error_response("Release channel is invalid.", exc)

    try:
        app = AppDefinition.objects.select_related("current_revision").get(tenant=context.tenant, app_id=app_id)
    except AppDefinition.DoesNotExist:
        return _not_found(f"App `{app_id}` was not found.")
    app_revision = app.current_revision
    if app_revision is None or app_revision.status != AppRevisionStatus.PUBLISHED:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message=f"App `{app_id}` must have a published current revision before packaging.",
                status_code=409,
            )
        )

    theme_id = str(payload.get("theme_id", app_revision.payload.get("theme_id", ""))).strip()
    if not theme_id:
        return validation_error_response("Package payload is invalid.", ValidationError({"theme_id": "Required."}))
    try:
        theme = Theme.objects.select_related("current_revision").get(tenant=context.tenant, theme_id=theme_id)
    except Theme.DoesNotExist:
        return _not_found(f"Theme `{theme_id}` was not found.")
    theme_revision = theme.current_revision
    if theme_revision is None or theme_revision.status != ThemeRevisionStatus.PUBLISHED:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message=f"Theme `{theme_id}` must have a published current revision before packaging.",
                status_code=409,
            )
        )

    requested_form_ids = payload.get("form_ids")
    form_ids = requested_form_ids if isinstance(requested_form_ids, list) else _form_ids_from_app_payload(app_revision.payload)
    if not form_ids:
        return validation_error_response(
            "Package payload is invalid.",
            ValidationError({"form_ids": "At least one referenced form is required."}),
        )

    form_revisions = []
    for form_id in form_ids:
        if not isinstance(form_id, str) or not form_id.strip():
            return validation_error_response(
                "Package payload is invalid.",
                ValidationError({"form_ids": "Form IDs must be non-empty strings."}),
            )
        form_id = form_id.strip()
        try:
            form = FormDefinition.objects.select_related("current_revision").get(
                tenant=context.tenant,
                form_id=form_id,
            )
        except FormDefinition.DoesNotExist:
            return _not_found(f"Form `{form_id}` was not found.")
        form_revision = form.current_revision
        if form_revision is None or form_revision.status != FormRevisionStatus.PUBLISHED:
            return api_error_response(
                ApiError(
                    code=ApiErrorCode.CONFLICT,
                    message=f"Form `{form_id}` must have a published current revision before packaging.",
                    status_code=409,
                )
            )
        form_revisions.append(form_revision)

    module_registrations = list(
        ModuleRegistration.objects.filter(status=ModuleRegistrationStatus.ENABLED).order_by("module_id", "version")
    )
    if not module_registrations:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message="At least one enabled module registration is required before packaging.",
                status_code=409,
            )
        )

    user = getattr(request, "user", None)
    created_by = user.username if getattr(user, "is_authenticated", False) else "builder"
    try:
        package = compile_deployment_package(
            tenant=context.tenant,
            package_id=package_id,
            app_revision=app_revision,
            theme_revision=theme_revision,
            form_revisions=form_revisions,
            module_registrations=module_registrations,
            runtime_min_version=runtime_min_version,
            runtime_max_version=runtime_max_version,
            channel=channel,
            platform_version=platform_version,
            created_by=created_by,
            signing_key=signing_key,
        )
    except ValidationError as exc:
        return validation_error_response("Deployment package is invalid.", exc)
    except IntegrityError:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message=f"Package `{package_id}` or app version `{app_revision.version}` already exists on `{channel}`.",
                status_code=409,
            )
        )

    return JsonResponse({"package": _serialize_admin_package(package, include_payload=True)}, status=201)


def admin_package_activate(request: HttpRequest, package_id: str) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    context = require_tenant_context(request, permission="builder.package.publish")
    if isinstance(context, JsonResponse):
        return context

    try:
        package = DeploymentPackage.objects.get(tenant=context.tenant, package_id=package_id)
    except DeploymentPackage.DoesNotExist:
        return _not_found(f"Package `{package_id}` was not found.")

    try:
        package = activate_deployment_package(package)
    except ValidationError as exc:
        return validation_error_response("Deployment package could not be activated.", exc)

    return JsonResponse({"package": _serialize_admin_package(package, include_payload=True)})


def active_package_manifest(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    app_id = required_query_param(request, "app_id")
    if isinstance(app_id, JsonResponse):
        return app_id

    channel = request.GET.get("channel", "dev").strip() or "dev"
    try:
        validate_release_channel_name(channel)
    except ValidationError as exc:
        return validation_error_response("Release channel is invalid.", exc)

    package = active_deployment_package(tenant=tenant, app_id=app_id, channel=channel)
    if package is None:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"No active package was found for app `{app_id}` on channel `{channel}`.",
                status_code=404,
            )
        )

    return JsonResponse({"manifest": _serialize_package_manifest(package)})


def package_download(request: HttpRequest, package_id: str) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    try:
        package = DeploymentPackage.objects.get(tenant=tenant, package_id=package_id)
    except DeploymentPackage.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Package `{package_id}` was not found.",
                status_code=404,
            )
        )

    if package.status != DeploymentPackageStatus.ACTIVE:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message=f"Package `{package_id}` is not active.",
                status_code=409,
            )
        )

    response = JsonResponse(
        {
            "manifest": _serialize_package_manifest(package),
            "package": package.payload,
        }
    )
    response["ETag"] = f'"{package.package_hash}"'
    return response
