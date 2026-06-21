from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit.models import AuditEvent, AuditEventType, AuditSeverity
from apps.form_builder.models import FormDefinition, FormRevisionStatus, FormSubmission

from .models import (
    OutboxBatch,
    SubmissionSyncResult,
    SyncBatchStatus,
    SyncDevice,
    SyncRejectionReason,
    SyncSession,
    SyncSubmissionStatus,
)


@dataclass(frozen=True)
class SyncSubmissionReceipt:
    client_submission_id: str
    form_id: str
    reason_code: str
    message: str
    status: str
    submission_id: int | None = None


@dataclass(frozen=True)
class SyncBatchReceipt:
    accepted_count: int
    batch: OutboxBatch
    duplicate_count: int
    receipts: list[SyncSubmissionReceipt]
    rejected_count: int
    session: SyncSession


def register_sync_device(
    *,
    tenant,
    device_id: str,
    platform: str,
    app_version: str = "",
    runtime_version: str = "",
) -> SyncDevice:
    if not device_id:
        raise ValidationError({"device_id": "Required."})
    if not platform:
        raise ValidationError({"platform": "Required."})

    device, _created = SyncDevice.objects.update_or_create(
        tenant=tenant,
        device_id=device_id,
        defaults={
            "app_version": app_version,
            "platform": platform,
            "runtime_version": runtime_version,
        },
    )
    return device


@transaction.atomic
def submit_outbox_batch(*, tenant, payload: dict[str, Any]) -> SyncBatchReceipt:
    device_id = _required_string(payload, "device_id")
    batch_id = _required_string(payload, "batch_id")
    submissions = payload.get("submissions")
    if not isinstance(submissions, list):
        raise ValidationError({"submissions": "Must be a list."})

    device = register_sync_device(
        tenant=tenant,
        device_id=device_id,
        platform=str(payload.get("platform", "unknown")).strip() or "unknown",
        app_version=str(payload.get("app_version", "")).strip(),
        runtime_version=str(payload.get("runtime_version", "")).strip(),
    )
    existing_batch = (
        OutboxBatch.objects.filter(tenant=tenant, device=device, batch_id=batch_id)
        .select_related("session")
        .prefetch_related("results__form_submission", "results__rejection_reason")
        .first()
    )
    if existing_batch is not None:
        return _receipt_from_existing_batch(existing_batch)

    session = SyncSession.objects.create(tenant=tenant, device=device)
    batch = OutboxBatch.objects.create(
        tenant=tenant,
        batch_id=batch_id,
        device=device,
        session=session,
        status=SyncBatchStatus.ACCEPTED,
        payload=payload,
    )

    receipts = [_process_submission(tenant=tenant, batch=batch, item=item) for item in submissions]
    accepted_count = sum(1 for receipt in receipts if receipt.status == SyncSubmissionStatus.ACCEPTED)
    duplicate_count = sum(1 for receipt in receipts if receipt.status == SyncSubmissionStatus.DUPLICATE)
    rejected_count = sum(1 for receipt in receipts if receipt.status == SyncSubmissionStatus.REJECTED)
    status = _batch_status(accepted_count=accepted_count, duplicate_count=duplicate_count, rejected_count=rejected_count)

    batch.accepted_count = accepted_count
    batch.duplicate_count = duplicate_count
    batch.rejected_count = rejected_count
    batch.status = status
    batch.save(update_fields=["accepted_count", "duplicate_count", "rejected_count", "status", "updated_at"])
    session.accepted_count = accepted_count
    session.duplicate_count = duplicate_count
    session.rejected_count = rejected_count
    session.status = status
    session.save(update_fields=["accepted_count", "duplicate_count", "rejected_count", "status", "updated_at"])

    return SyncBatchReceipt(
        accepted_count=accepted_count,
        batch=batch,
        duplicate_count=duplicate_count,
        receipts=receipts,
        rejected_count=rejected_count,
        session=session,
    )


def _receipt_from_existing_batch(batch: OutboxBatch) -> SyncBatchReceipt:
    receipts = [_receipt_from_result(result) for result in batch.results.all()]
    return SyncBatchReceipt(
        accepted_count=batch.accepted_count,
        batch=batch,
        duplicate_count=batch.duplicate_count,
        receipts=receipts,
        rejected_count=batch.rejected_count,
        session=batch.session,
    )


def _receipt_from_result(result: SubmissionSyncResult) -> SyncSubmissionReceipt:
    reason = result.rejection_reason
    form_submission = result.form_submission
    form_id = form_submission.form.form_id if form_submission is not None else ""
    if form_submission is not None:
        message = "Submission accepted."
        reason_code = "accepted"
    elif reason is not None:
        message = reason.message
        reason_code = reason.code
    else:
        message = "Submission was already processed."
        reason_code = "duplicate"
    return SyncSubmissionReceipt(
        client_submission_id=result.client_submission_id,
        form_id=form_id,
        message=message,
        reason_code=reason_code,
        status=result.status,
        submission_id=result.form_submission_id,
    )


def _process_submission(*, tenant, batch: OutboxBatch, item: Any) -> SyncSubmissionReceipt:
    if not isinstance(item, dict):
        return _reject(tenant=tenant, batch=batch, client_submission_id="", form_id="", code="invalid_payload", message="Submission must be a JSON object.")

    client_submission_id = str(item.get("client_submission_id", "")).strip()
    form_id = str(item.get("form_id", "")).strip()
    answers = item.get("answers")

    if not client_submission_id:
        return _reject(tenant=tenant, batch=batch, client_submission_id="", form_id=form_id, code="missing_client_submission_id", message="client_submission_id is required.")

    existing = SubmissionSyncResult.objects.filter(
        tenant=tenant,
        client_submission_id=client_submission_id,
    ).select_related("form_submission", "rejection_reason").first()
    if existing is not None:
        return _duplicate_receipt(client_submission_id=client_submission_id, form_id=form_id, existing=existing)

    if not form_id:
        return _reject(tenant=tenant, batch=batch, client_submission_id=client_submission_id, form_id="", code="missing_form_id", message="form_id is required.")
    if not isinstance(answers, dict):
        return _reject(tenant=tenant, batch=batch, client_submission_id=client_submission_id, form_id=form_id, code="invalid_answers", message="answers must be a JSON object.")

    try:
        form = FormDefinition.objects.select_related("current_revision").get(tenant=tenant, form_id=form_id)
    except FormDefinition.DoesNotExist:
        return _reject(tenant=tenant, batch=batch, client_submission_id=client_submission_id, form_id=form_id, code="unknown_form", message=f"Form `{form_id}` was not found.")

    revision = form.current_revision
    if revision is None or revision.status != FormRevisionStatus.PUBLISHED:
        return _reject(tenant=tenant, batch=batch, client_submission_id=client_submission_id, form_id=form_id, code="form_not_published", message=f"Form `{form_id}` does not have a published revision.")

    submission = FormSubmission.objects.create(
        tenant=tenant,
        form=form,
        revision=revision,
        answers=answers,
    )
    SubmissionSyncResult.objects.create(
        tenant=tenant,
        batch=batch,
        client_submission_id=client_submission_id,
        form_submission=submission,
        status=SyncSubmissionStatus.ACCEPTED,
    )
    AuditEvent.objects.create(
        tenant=tenant,
        event_type=AuditEventType.SYNC,
        action="sync-submission-accepted",
        target_type="form_submission",
        target_id=str(submission.id),
        target_repr=f"{form.form_id}:{client_submission_id}",
        metadata={
            "batch_id": batch.batch_id,
            "client_submission_id": client_submission_id,
            "form_id": form_id,
        },
    )
    return SyncSubmissionReceipt(
        client_submission_id=client_submission_id,
        form_id=form_id,
        message="Submission accepted.",
        reason_code="accepted",
        status=SyncSubmissionStatus.ACCEPTED,
        submission_id=submission.id,
    )


def _duplicate_receipt(*, client_submission_id: str, form_id: str, existing: SubmissionSyncResult) -> SyncSubmissionReceipt:
    if not form_id and existing.form_submission is not None:
        form_id = existing.form_submission.form.form_id
    return SyncSubmissionReceipt(
        client_submission_id=client_submission_id,
        form_id=form_id,
        message="Submission was already processed.",
        reason_code="duplicate",
        status=SyncSubmissionStatus.DUPLICATE,
        submission_id=existing.form_submission_id,
    )


def _reject(
    *,
    tenant,
    batch: OutboxBatch,
    client_submission_id: str,
    form_id: str,
    code: str,
    message: str,
) -> SyncSubmissionReceipt:
    reason, _created = SyncRejectionReason.objects.get_or_create(
        tenant=tenant,
        code=code,
        message=message,
    )
    if client_submission_id:
        SubmissionSyncResult.objects.create(
            tenant=tenant,
            batch=batch,
            client_submission_id=client_submission_id,
            rejection_reason=reason,
            status=SyncSubmissionStatus.REJECTED,
        )
    AuditEvent.objects.create(
        tenant=tenant,
        event_type=AuditEventType.SYNC,
        severity=AuditSeverity.WARNING,
        action="sync-submission-rejected",
        target_type="sync_submission",
        target_id=client_submission_id,
        metadata={
            "batch_id": batch.batch_id,
            "client_submission_id": client_submission_id,
            "form_id": form_id,
            "reason_code": code,
        },
    )
    return SyncSubmissionReceipt(
        client_submission_id=client_submission_id,
        form_id=form_id,
        message=message,
        reason_code=code,
        status=SyncSubmissionStatus.REJECTED,
    )


def _batch_status(*, accepted_count: int, duplicate_count: int, rejected_count: int) -> str:
    if rejected_count and not accepted_count and not duplicate_count:
        return SyncBatchStatus.REJECTED
    if rejected_count:
        return SyncBatchStatus.PARTIAL
    return SyncBatchStatus.ACCEPTED


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = str(payload.get(field, "")).strip()
    if not value:
        raise ValidationError({field: "Required."})
    return value
