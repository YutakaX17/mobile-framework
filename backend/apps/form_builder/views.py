from __future__ import annotations

import json
from json import JSONDecodeError

from django.http import HttpRequest, JsonResponse

from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response
from apps.tenants.models import Tenant

from .models import FormDefinition, FormRevision, FormRevisionStatus, FormSubmission


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


def _field_count(revision: FormRevision | None) -> int:
    if revision is None:
        return 0
    fields = revision.payload.get("fields", [])
    return len(fields) if isinstance(fields, list) else 0


def _serialize_revision(revision: FormRevision | None, include_payload: bool = False) -> dict | None:
    if revision is None:
        return None

    data = {
        "field_count": _field_count(revision),
        "revision": revision.revision,
        "schema_version": revision.schema_version,
        "status": revision.status,
        "version": revision.version,
    }
    if include_payload:
        data["payload"] = revision.payload
    return data


def _serialize_form_summary(form: FormDefinition) -> dict:
    return {
        "current_revision": _serialize_revision(form.current_revision),
        "description": form.description,
        "form_id": form.form_id,
        "mode": form.mode,
        "name": form.name,
    }


def _serialize_submission(submission: FormSubmission) -> dict:
    return {
        "answer_count": submission.answer_count,
        "form_id": submission.form.form_id,
        "id": submission.id,
        "revision": submission.revision.revision,
        "status": submission.status,
    }


def _json_payload_from_request(request: HttpRequest) -> dict | JsonResponse:
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


def _answers_from_payload(payload: dict) -> dict | JsonResponse:
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        return api_error_response(
            ApiError(
                code=ApiErrorCode.VALIDATION_ERROR,
                message="Submission answers must be a JSON object.",
                details=[ApiErrorDetail(field="answers", message="Provide answers as a JSON object.")],
                status_code=400,
            )
        )
    return answers


def form_list(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    forms = (
        FormDefinition.objects.select_related("current_revision")
        .filter(tenant=tenant)
        .order_by("form_id")
    )
    return JsonResponse({"forms": [_serialize_form_summary(form) for form in forms]})


def form_detail(request: HttpRequest, form_id: str) -> JsonResponse:
    if request.method != "GET":
        return _method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    try:
        form = FormDefinition.objects.select_related("current_revision").get(tenant=tenant, form_id=form_id)
    except FormDefinition.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Form `{form_id}` was not found.",
                status_code=404,
            )
        )

    data = _serialize_form_summary(form)
    data["current_revision"] = _serialize_revision(form.current_revision, include_payload=True)
    return JsonResponse({"form": data})


def form_submit(request: HttpRequest, form_id: str) -> JsonResponse:
    if request.method != "POST":
        return _method_not_allowed("POST")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    try:
        form = FormDefinition.objects.select_related("current_revision").get(tenant=tenant, form_id=form_id)
    except FormDefinition.DoesNotExist:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.NOT_FOUND,
                message=f"Form `{form_id}` was not found.",
                status_code=404,
            )
        )

    if form.current_revision is None:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message=f"Form `{form_id}` does not have a current revision.",
                status_code=409,
            )
        )
    if form.current_revision.status != FormRevisionStatus.PUBLISHED:
        return api_error_response(
            ApiError(
                code=ApiErrorCode.CONFLICT,
                message=f"Form `{form_id}` current revision is not published.",
                status_code=409,
            )
        )

    payload = _json_payload_from_request(request)
    if isinstance(payload, JsonResponse):
        return payload
    answers = _answers_from_payload(payload)
    if isinstance(answers, JsonResponse):
        return answers

    user = getattr(request, "user", None)
    submitted_by = user if getattr(user, "is_authenticated", False) else None
    submission = FormSubmission.objects.create(
        tenant=tenant,
        form=form,
        revision=form.current_revision,
        answers=answers,
        submitted_by=submitted_by,
    )
    return JsonResponse({"submission": _serialize_submission(submission)}, status=201)
