from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max

from apps.tenants.models import TenantScopedModel

from .services import validate_theme_payload


class ThemeRevisionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    VALIDATED = "validated", "Validated"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"
    REJECTED = "rejected", "Rejected"


class Theme(TenantScopedModel):
    theme_id = models.SlugField(max_length=80)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    current_revision = models.ForeignKey(
        "ThemeRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["tenant__slug", "theme_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "theme_id"], name="unique_theme_id_per_tenant"),
        ]

    @classmethod
    def from_payload(cls, tenant, payload: dict):
        return cls(
            tenant=tenant,
            theme_id=payload["theme_id"],
            name=payload["name"],
            description=payload.get("description", ""),
        )

    def clean(self) -> None:
        super().clean()
        if self.current_revision_id and self.current_revision.theme_id != self.id:
            raise ValidationError({"current_revision": "Must belong to this theme."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.theme_id}"


class ThemeRevision(TenantScopedModel):
    theme = models.ForeignKey(Theme, related_name="revisions", on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    version = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=16, default="v1")
    status = models.CharField(
        max_length=16,
        choices=ThemeRevisionStatus.choices,
        default=ThemeRevisionStatus.DRAFT,
        db_index=True,
    )
    payload = models.JSONField()
    validation_errors = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="theme_revisions",
    )

    class Meta:
        ordering = ["theme_id", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["theme", "revision"], name="unique_theme_revision_number"),
        ]

    @classmethod
    def next_revision_number(cls, theme: Theme) -> int:
        latest = cls.objects.filter(theme=theme).aggregate(max_revision=Max("revision"))["max_revision"]
        return (latest or 0) + 1

    @classmethod
    def create_next(cls, theme: Theme, payload: dict, **kwargs):
        return cls.objects.create(
            tenant=theme.tenant,
            theme=theme,
            revision=cls.next_revision_number(theme),
            schema_version=payload.get("schema_version", "v1"),
            version=payload["version"],
            payload=payload,
            **kwargs,
        )

    def clean(self) -> None:
        super().clean()
        if self.theme_id and self.tenant_id != self.theme.tenant_id:
            raise ValidationError({"tenant": "Must match the theme tenant."})
        validate_theme_payload(self.payload)
        expected_values = {
            "theme_id": self.theme.theme_id if self.theme_id else None,
            "name": self.theme.name if self.theme_id else None,
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
        return f"{self.theme}#{self.revision}"
