from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max

from apps.tenants.models import TenantScopedModel

from .services import validate_app_payload


class AppRevisionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEWED = "reviewed", "Reviewed"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class AppDefinition(TenantScopedModel):
    app_id = models.SlugField(max_length=80)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    current_revision = models.ForeignKey(
        "AppRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["tenant__slug", "app_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "app_id"], name="unique_app_id_per_tenant"),
        ]

    @classmethod
    def from_payload(cls, tenant, payload: dict):
        return cls(
            tenant=tenant,
            app_id=payload["app_id"],
            name=payload["name"],
            description=payload.get("description", ""),
        )

    def clean(self) -> None:
        super().clean()
        if self.current_revision_id and self.current_revision.app_id != self.id:
            raise ValidationError({"current_revision": "Must belong to this app definition."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.app_id}"


class AppRevision(TenantScopedModel):
    app = models.ForeignKey(AppDefinition, related_name="revisions", on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    version = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=16, default="v1")
    status = models.CharField(
        max_length=16,
        choices=AppRevisionStatus.choices,
        default=AppRevisionStatus.DRAFT,
        db_index=True,
    )
    payload = models.JSONField()
    validation_errors = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="app_revisions",
    )

    class Meta:
        ordering = ["app_id", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["app", "revision"], name="unique_app_revision_number"),
        ]

    @classmethod
    def next_revision_number(cls, app: AppDefinition) -> int:
        latest = cls.objects.filter(app=app).aggregate(max_revision=Max("revision"))["max_revision"]
        return (latest or 0) + 1

    @classmethod
    def create_next(cls, app: AppDefinition, payload: dict, **kwargs):
        return cls.objects.create(
            tenant=app.tenant,
            app=app,
            revision=cls.next_revision_number(app),
            schema_version=payload.get("schema_version", "v1"),
            version=payload["version"],
            payload=payload,
            **kwargs,
        )

    def clean(self) -> None:
        super().clean()
        if self.app_id and self.tenant_id != self.app.tenant_id:
            raise ValidationError({"tenant": "Must match the app definition tenant."})
        validate_app_payload(self.payload)
        expected_values = {
            "app_id": self.app.app_id if self.app_id else None,
            "name": self.app.name if self.app_id else None,
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
        return f"{self.app}#{self.revision}"
