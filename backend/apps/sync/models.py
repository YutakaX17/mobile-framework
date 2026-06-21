from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.form_builder.models import FormSubmission
from apps.tenants.models import TenantScopedModel


class SyncDeviceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    BLOCKED = "blocked", "Blocked"


class SyncBatchStatus(models.TextChoices):
    ACCEPTED = "accepted", "Accepted"
    PARTIAL = "partial", "Partial"
    REJECTED = "rejected", "Rejected"


class SyncSubmissionStatus(models.TextChoices):
    ACCEPTED = "accepted", "Accepted"
    DUPLICATE = "duplicate", "Duplicate"
    REJECTED = "rejected", "Rejected"


class SyncDevice(TenantScopedModel):
    device_id = models.SlugField(max_length=128)
    platform = models.CharField(max_length=64)
    app_version = models.CharField(max_length=80, blank=True)
    runtime_version = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=16,
        choices=SyncDeviceStatus.choices,
        default=SyncDeviceStatus.ACTIVE,
        db_index=True,
    )
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["tenant__slug", "device_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "device_id"], name="unique_sync_device_per_tenant"),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.device_id}"


class SyncSession(TenantScopedModel):
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    device = models.ForeignKey(SyncDevice, related_name="sessions", on_delete=models.PROTECT)
    status = models.CharField(
        max_length=16,
        choices=SyncBatchStatus.choices,
        default=SyncBatchStatus.ACCEPTED,
        db_index=True,
    )
    accepted_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    rejected_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-id"]

    def clean(self) -> None:
        super().clean()
        if self.device_id and self.tenant_id != self.device.tenant_id:
            raise ValidationError({"tenant": "Must match the sync device tenant."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.device}:{self.session_id}"


class OutboxBatch(TenantScopedModel):
    batch_id = models.SlugField(max_length=128)
    device = models.ForeignKey(SyncDevice, related_name="outbox_batches", on_delete=models.PROTECT)
    session = models.ForeignKey(SyncSession, related_name="batches", on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=SyncBatchStatus.choices, db_index=True)
    payload = models.JSONField(default=dict)
    accepted_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    rejected_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "device", "batch_id"], name="unique_outbox_batch_per_device"),
        ]

    def clean(self) -> None:
        super().clean()
        if self.device_id and self.tenant_id != self.device.tenant_id:
            raise ValidationError({"tenant": "Must match the sync device tenant."})
        if self.session_id and self.tenant_id != self.session.tenant_id:
            raise ValidationError({"tenant": "Must match the sync session tenant."})
        if not isinstance(self.payload, dict):
            raise ValidationError({"payload": "Must be a JSON object."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.device}:{self.batch_id}"


class SyncRejectionReason(TenantScopedModel):
    code = models.SlugField(max_length=80)
    message = models.TextField()

    class Meta:
        ordering = ["tenant__slug", "code"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code", "message"], name="unique_sync_rejection_reason"),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.code}"


class SubmissionSyncResult(TenantScopedModel):
    batch = models.ForeignKey(OutboxBatch, related_name="results", on_delete=models.PROTECT)
    client_submission_id = models.SlugField(max_length=128)
    form_submission = models.ForeignKey(
        FormSubmission,
        null=True,
        blank=True,
        related_name="sync_results",
        on_delete=models.PROTECT,
    )
    rejection_reason = models.ForeignKey(
        SyncRejectionReason,
        null=True,
        blank=True,
        related_name="sync_results",
        on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=16, choices=SyncSubmissionStatus.choices, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "client_submission_id"],
                name="unique_sync_client_submission_per_tenant",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.batch_id and self.tenant_id != self.batch.tenant_id:
            raise ValidationError({"tenant": "Must match the outbox batch tenant."})
        if self.form_submission_id and self.tenant_id != self.form_submission.tenant_id:
            raise ValidationError({"tenant": "Must match the form submission tenant."})
        if self.rejection_reason_id and self.tenant_id != self.rejection_reason.tenant_id:
            raise ValidationError({"tenant": "Must match the rejection reason tenant."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.client_submission_id}:{self.status}"
