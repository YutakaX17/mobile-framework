from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max

from apps.tenants.models import TenantScopedModel

from .services import validate_configuration_payload


class ConfigurationKind(models.TextChoices):
    ACTION = "action", "Action"
    APP = "app", "App"
    DEPLOYMENT_PACKAGE = "deployment_package", "Deployment package"
    FIELD = "field", "Field"
    FORM = "form", "Form"
    SCREEN = "screen", "Screen"
    THEME = "theme", "Theme"


class ConfigurationRevisionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    VALIDATED = "validated", "Validated"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"
    REJECTED = "rejected", "Rejected"


class ConfigurationDefinition(TenantScopedModel):
    key = models.SlugField(max_length=120)
    kind = models.CharField(max_length=32, choices=ConfigurationKind.choices)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    current_revision = models.ForeignKey(
        "ConfigurationRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["tenant__slug", "kind", "key"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "kind", "key"], name="unique_configuration_definition_key"),
        ]

    def clean(self) -> None:
        super().clean()
        if self.current_revision_id and self.current_revision.definition_id != self.id:
            raise ValidationError({"current_revision": "Must belong to this configuration definition."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.kind}:{self.key}"


class ConfigurationRevision(TenantScopedModel):
    definition = models.ForeignKey(ConfigurationDefinition, related_name="revisions", on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    schema_version = models.CharField(max_length=16, default="v1")
    status = models.CharField(
        max_length=16,
        choices=ConfigurationRevisionStatus.choices,
        default=ConfigurationRevisionStatus.DRAFT,
        db_index=True,
    )
    payload = models.JSONField()
    validation_errors = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="configuration_revisions",
    )

    class Meta:
        ordering = ["definition_id", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["definition", "revision"], name="unique_configuration_revision_number"),
        ]

    @classmethod
    def next_revision_number(cls, definition: ConfigurationDefinition) -> int:
        latest = cls.objects.filter(definition=definition).aggregate(max_revision=Max("revision"))["max_revision"]
        return (latest or 0) + 1

    @classmethod
    def create_next(cls, definition: ConfigurationDefinition, payload: dict, **kwargs):
        return cls.objects.create(
            tenant=definition.tenant,
            definition=definition,
            revision=cls.next_revision_number(definition),
            payload=payload,
            **kwargs,
        )

    def clean(self) -> None:
        super().clean()
        if self.definition_id and self.tenant_id != self.definition.tenant_id:
            raise ValidationError({"tenant": "Must match the configuration definition tenant."})
        if self.definition_id:
            validate_configuration_payload(self.definition.kind, self.payload)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.definition}#{self.revision}"
