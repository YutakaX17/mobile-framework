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


class WorkflowTaskStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class WorkflowTaskAssignmentType(models.TextChoices):
    ROLE = "role", "Role"
    USER = "user", "User"
    EXPRESSION = "expression", "Expression"


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


class WorkflowTask(TenantScopedModel):
    workflow = models.ForeignKey(WorkflowDefinition, related_name="tasks", on_delete=models.PROTECT)
    revision = models.ForeignKey(WorkflowRevision, related_name="tasks", on_delete=models.PROTECT)
    task_key = models.SlugField(max_length=120)
    subject = models.CharField(max_length=200)
    current_state = models.SlugField(max_length=80)
    status = models.CharField(
        max_length=16,
        choices=WorkflowTaskStatus.choices,
        default=WorkflowTaskStatus.OPEN,
        db_index=True,
    )
    context = models.JSONField(default=dict, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["tenant__slug", "status", "due_at", "task_key"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "task_key"], name="unique_workflow_task_key_per_tenant"),
        ]

    @classmethod
    def create_for_revision(cls, revision: WorkflowRevision, task_key: str, subject: str, **kwargs):
        return cls.objects.create(
            tenant=revision.tenant,
            workflow=revision.workflow,
            revision=revision,
            task_key=task_key,
            subject=subject,
            current_state=kwargs.pop("current_state", revision.payload["initial_state"]),
            **kwargs,
        )

    @property
    def context_size(self) -> int:
        return len(self.context) if isinstance(self.context, dict) else 0

    def clean(self) -> None:
        super().clean()
        if self.workflow_id and self.tenant_id != self.workflow.tenant_id:
            raise ValidationError({"tenant": "Must match the workflow definition tenant."})
        if self.revision_id and self.tenant_id != self.revision.tenant_id:
            raise ValidationError({"tenant": "Must match the workflow revision tenant."})
        if self.workflow_id and self.revision_id and self.revision.workflow_id != self.workflow_id:
            raise ValidationError({"revision": "Must belong to the workflow definition."})
        if not isinstance(self.context, dict):
            raise ValidationError({"context": "Must be a JSON object."})
        if self.revision_id:
            state_ids = {state["state_id"] for state in self.revision.payload.get("states", [])}
            if self.current_state not in state_ids:
                raise ValidationError({"current_state": "Must reference a workflow revision state."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.workflow}:{self.task_key}"


class WorkflowTaskAssignment(TenantScopedModel):
    task = models.ForeignKey(WorkflowTask, related_name="assignments", on_delete=models.CASCADE)
    assignment_type = models.CharField(max_length=16, choices=WorkflowTaskAssignmentType.choices)
    role = models.CharField(max_length=120, blank=True)
    user_id = models.CharField(max_length=120, blank=True)
    expression = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["tenant__slug", "task_id", "assignment_type", "id"]

    @classmethod
    def assign_role(cls, task: WorkflowTask, role: str, **kwargs):
        return cls.objects.create(
            tenant=task.tenant,
            task=task,
            assignment_type=WorkflowTaskAssignmentType.ROLE,
            role=role,
            **kwargs,
        )

    @classmethod
    def assign_user(cls, task: WorkflowTask, user_id: str, **kwargs):
        return cls.objects.create(
            tenant=task.tenant,
            task=task,
            assignment_type=WorkflowTaskAssignmentType.USER,
            user_id=user_id,
            **kwargs,
        )

    @classmethod
    def assign_expression(cls, task: WorkflowTask, expression: str, **kwargs):
        return cls.objects.create(
            tenant=task.tenant,
            task=task,
            assignment_type=WorkflowTaskAssignmentType.EXPRESSION,
            expression=expression,
            **kwargs,
        )

    @property
    def target(self) -> str:
        if self.assignment_type == WorkflowTaskAssignmentType.ROLE:
            return self.role
        if self.assignment_type == WorkflowTaskAssignmentType.USER:
            return self.user_id
        return self.expression

    def clean(self) -> None:
        super().clean()
        if self.task_id and self.tenant_id != self.task.tenant_id:
            raise ValidationError({"tenant": "Must match the workflow task tenant."})

        required_fields = {
            WorkflowTaskAssignmentType.ROLE: "role",
            WorkflowTaskAssignmentType.USER: "user_id",
            WorkflowTaskAssignmentType.EXPRESSION: "expression",
        }
        required_field = required_fields.get(self.assignment_type)
        if required_field and not getattr(self, required_field):
            raise ValidationError({required_field: "Required for this assignment type."})

        inactive_fields = set(required_fields.values()) - {required_field}
        for field_name in inactive_fields:
            if getattr(self, field_name):
                raise ValidationError({field_name: "Must be blank for this assignment type."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.task}:{self.assignment_type}:{self.target}"
