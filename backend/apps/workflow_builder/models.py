from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max

from apps.tenants.models import TenantScopedModel

from .services import validate_workflow_payload


class WorkflowRevisionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEWED = "reviewed", "Reviewed"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class WorkflowDefinition(TenantScopedModel):
    workflow_id = models.SlugField(max_length=80)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    current_revision = models.ForeignKey(
        "WorkflowRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["tenant__slug", "workflow_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "workflow_id"], name="unique_workflow_id_per_tenant"),
        ]

    @classmethod
    def from_payload(cls, tenant, payload: dict):
        return cls(
            tenant=tenant,
            workflow_id=payload["workflow_id"],
            name=payload["name"],
            description=payload.get("description", ""),
        )

    def clean(self) -> None:
        super().clean()
        if self.current_revision_id and self.current_revision.workflow_id != self.id:
            raise ValidationError({"current_revision": "Must belong to this workflow definition."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.workflow_id}"


class WorkflowRevision(TenantScopedModel):
    workflow = models.ForeignKey(WorkflowDefinition, related_name="revisions", on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    version = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=16, default="v1")
    status = models.CharField(
        max_length=16,
        choices=WorkflowRevisionStatus.choices,
        default=WorkflowRevisionStatus.DRAFT,
        db_index=True,
    )
    payload = models.JSONField()
    validation_errors = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="workflow_revisions",
    )

    class Meta:
        ordering = ["workflow_id", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["workflow", "revision"], name="unique_workflow_revision_number"),
        ]

    @classmethod
    def next_revision_number(cls, workflow: WorkflowDefinition) -> int:
        latest = cls.objects.filter(workflow=workflow).aggregate(max_revision=Max("revision"))["max_revision"]
        return (latest or 0) + 1

    @classmethod
    def create_next(cls, workflow: WorkflowDefinition, payload: dict, **kwargs):
        return cls.objects.create(
            tenant=workflow.tenant,
            workflow=workflow,
            revision=cls.next_revision_number(workflow),
            schema_version=payload.get("schema_version", "v1"),
            version=payload["version"],
            payload=payload,
            **kwargs,
        )

    def clean(self) -> None:
        super().clean()
        if self.workflow_id and self.tenant_id != self.workflow.tenant_id:
            raise ValidationError({"tenant": "Must match the workflow definition tenant."})
        validate_workflow_payload(self.payload)
        expected_values = {
            "workflow_id": self.workflow.workflow_id if self.workflow_id else None,
            "name": self.workflow.name if self.workflow_id else None,
            "schema_version": self.schema_version,
            "version": self.version,
        }
        for key, expected in expected_values.items():
            if expected is not None and self.payload.get(key) != expected:
                raise ValidationError({key: f"Must match payload field `{key}`."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.workflow}#{self.revision}"
