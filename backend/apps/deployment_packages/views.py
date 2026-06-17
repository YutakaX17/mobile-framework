from __future__ import annotations

from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse

from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response
from apps.tenants.models import Tenant

from .models import DeploymentPackage, DeploymentPackageStatus
from .services import active_deployment_package, validate_release_channel_name


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


def _required_query_param(request: HttpRequest, name: str) -> str | JsonResponse:
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


def _validation_error_response(message: str, error: ValidationError) -> JsonResponse:
    details: list[ApiErrorDetail] = []
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


def active_package_manifest(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    app_id = _required_query_param(request, "app_id")
    if isinstance(app_id, JsonResponse):
        return app_id

    channel = request.GET.get("channel", "dev").strip() or "dev"
    try:
        validate_release_channel_name(channel)
    except ValidationError as exc:
        return _validation_error_response("Release channel is invalid.", exc)

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
        return _method_not_allowed("GET")

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
