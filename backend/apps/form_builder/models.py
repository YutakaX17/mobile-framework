from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max

from apps.tenants.models import TenantScopedModel

from .services import validate_form_payload


class FormRevisionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEWED = "reviewed", "Reviewed"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class FormDefinition(TenantScopedModel):
    form_id = models.SlugField(max_length=80)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    mode = models.CharField(max_length=16)
    current_revision = models.ForeignKey(
        "FormRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["tenant__slug", "form_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "form_id"], name="unique_form_id_per_tenant"),
        ]

    @classmethod
    def from_payload(cls, tenant, payload: dict):
        return cls(
            tenant=tenant,
            form_id=payload["form_id"],
            name=payload["name"],
            description=payload.get("description", ""),
            mode=payload["mode"],
        )

    def clean(self) -> None:
        super().clean()
        if self.current_revision_id and self.current_revision.form_id != self.id:
            raise ValidationError({"current_revision": "Must belong to this form definition."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.form_id}"


class FormRevision(TenantScopedModel):
    form = models.ForeignKey(FormDefinition, related_name="revisions", on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    version = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=16, default="v1")
    status = models.CharField(
        max_length=16,
        choices=FormRevisionStatus.choices,
        default=FormRevisionStatus.DRAFT,
        db_index=True,
    )
    payload = models.JSONField()
    validation_errors = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="form_revisions",
    )

    class Meta:
        ordering = ["form_id", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["form", "revision"], name="unique_form_revision_number"),
        ]

    @classmethod
    def next_revision_number(cls, form: FormDefinition) -> int:
        latest = cls.objects.filter(form=form).aggregate(max_revision=Max("revision"))["max_revision"]
        return (latest or 0) + 1

    @classmethod
    def create_next(cls, form: FormDefinition, payload: dict, **kwargs):
        return cls.objects.create(
            tenant=form.tenant,
            form=form,
            revision=cls.next_revision_number(form),
            schema_version=payload.get("schema_version", "v1"),
            version=payload["version"],
            payload=payload,
            **kwargs,
        )

    def clean(self) -> None:
        super().clean()
        if self.form_id and self.tenant_id != self.form.tenant_id:
            raise ValidationError({"tenant": "Must match the form definition tenant."})
        validate_form_payload(self.payload)
        expected_values = {
            "form_id": self.form.form_id if self.form_id else None,
            "name": self.form.name if self.form_id else None,
            "mode": self.form.mode if self.form_id else None,
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
        return f"{self.form}#{self.revision}"
