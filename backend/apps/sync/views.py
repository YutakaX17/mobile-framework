from __future__ import annotations

from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse

from apps.core.api import (
    json_payload_from_request,
    method_not_allowed,
    resolve_tenant_from_request,
    validation_error_response,
)

from .models import OutboxBatch, SubmissionSyncResult, SyncDevice
from .services import SyncBatchReceipt, register_sync_device, submit_outbox_batch


def _tenant_from_request(request: HttpRequest):
    context = resolve_tenant_from_request(request)
    if isinstance(context, JsonResponse):
        return context
    return context.tenant


def _serialize_device(device: SyncDevice) -> dict:
    return {
        "app_version": device.app_version,
        "device_id": device.device_id,
        "last_seen_at": device.last_seen_at.isoformat(),
        "platform": device.platform,
        "runtime_version": device.runtime_version,
        "status": device.status,
    }


def _serialize_result(result: SubmissionSyncResult) -> dict:
    reason = result.rejection_reason
    form_submission = result.form_submission
    form_id = form_submission.form.form_id if form_submission is not None else ""
    return {
        "client_submission_id": result.client_submission_id,
        "form_id": form_id,
        "message": reason.message if reason is not None else "",
        "reason_code": reason.code if reason is not None else "",
        "status": result.status,
        "submission_id": result.form_submission_id,
    }


def _serialize_batch(batch: OutboxBatch, include_results: bool = True) -> dict:
    data = {
        "accepted_count": batch.accepted_count,
        "batch_id": batch.batch_id,
        "created_at": batch.created_at.isoformat(),
        "device_id": batch.device.device_id,
        "duplicate_count": batch.duplicate_count,
        "rejected_count": batch.rejected_count,
        "session_id": str(batch.session.session_id),
        "status": batch.status,
        "updated_at": batch.updated_at.isoformat(),
    }
    if include_results:
        data["results"] = [_serialize_result(result) for result in batch.results.all()]
    return data


def _serialize_receipt(receipt: SyncBatchReceipt) -> dict:
    return {
        "batch": _serialize_batch(receipt.batch, include_results=False),
        "receipts": [
            {
                "client_submission_id": item.client_submission_id,
                "form_id": item.form_id,
                "message": item.message,
                "reason_code": item.reason_code,
                "status": item.status,
                "submission_id": item.submission_id,
            }
            for item in receipt.receipts
        ],
        "session": {
            "accepted_count": receipt.session.accepted_count,
            "duplicate_count": receipt.session.duplicate_count,
            "rejected_count": receipt.session.rejected_count,
            "session_id": str(receipt.session.session_id),
            "status": receipt.session.status,
        },
    }


def register_device(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    payload = json_payload_from_request(request)
    if isinstance(payload, JsonResponse):
        return payload

    try:
        device = register_sync_device(
            tenant=tenant,
            device_id=str(payload.get("device_id", "")).strip(),
            platform=str(payload.get("platform", "")).strip(),
            app_version=str(payload.get("app_version", "")).strip(),
            runtime_version=str(payload.get("runtime_version", "")).strip(),
        )
    except ValidationError as exc:
        return validation_error_response("Sync device payload is invalid.", exc)

    return JsonResponse({"device": _serialize_device(device)}, status=201)


def submit_outbox(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return method_not_allowed("POST")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    payload = json_payload_from_request(request)
    if isinstance(payload, JsonResponse):
        return payload

    try:
        receipt = submit_outbox_batch(tenant=tenant, payload=payload)
    except ValidationError as exc:
        return validation_error_response("Outbox payload is invalid.", exc)

    return JsonResponse(_serialize_receipt(receipt), status=202)


def sync_status(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return method_not_allowed("GET")

    tenant = _tenant_from_request(request)
    if isinstance(tenant, JsonResponse):
        return tenant

    devices = SyncDevice.objects.filter(tenant=tenant).order_by("device_id")
    device_id = request.GET.get("device_id", "").strip()
    if device_id:
        devices = devices.filter(device_id=device_id)

    batches = (
        OutboxBatch.objects.filter(tenant=tenant, device__in=devices)
        .select_related("device", "session")
        .prefetch_related("results__form_submission__form", "results__rejection_reason")
        .order_by("-created_at", "-id")[:20]
    )
    return JsonResponse(
        {
            "batches": [_serialize_batch(batch) for batch in batches],
            "devices": [_serialize_device(device) for device in devices],
        }
    )
