from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from .services import validate_module_manifest


class ModuleRegistrationStatus(models.TextChoices):
    REGISTERED = "registered", "Registered"
    ENABLED = "enabled", "Enabled"
    DISABLED = "disabled", "Disabled"
    DEPRECATED = "deprecated", "Deprecated"


class ModuleRegistration(models.Model):
    module_id = models.SlugField(max_length=80)
    name = models.CharField(max_length=120)
    version = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=16, default="v1")
    plugin_api_version = models.PositiveIntegerField()
    platform_min_version = models.CharField(max_length=80)
    platform_max_version = models.CharField(max_length=80, blank=True)
    manifest = models.JSONField()
    status = models.CharField(
        max_length=16,
        choices=ModuleRegistrationStatus.choices,
        default=ModuleRegistrationStatus.REGISTERED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module_id", "version"]
        constraints = [
            models.UniqueConstraint(fields=["module_id", "version"], name="unique_module_registration_version"),
        ]

    @classmethod
    def from_manifest(cls, manifest: dict):
        return cls(
            module_id=manifest["module_id"],
            name=manifest["name"],
            version=manifest["version"],
            schema_version=manifest["schema_version"],
            plugin_api_version=manifest["plugin_api_version"],
            platform_min_version=manifest["platform_min_version"],
            platform_max_version=manifest.get("platform_max_version", ""),
            manifest=manifest,
        )

    def clean(self) -> None:
        super().clean()
        validate_module_manifest(self.manifest)
        expected_values = {
            "module_id": self.module_id,
            "name": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
            "plugin_api_version": self.plugin_api_version,
            "platform_min_version": self.platform_min_version,
        }
        for key, expected in expected_values.items():
            if self.manifest.get(key) != expected:
                raise ValidationError({key: f"Must match manifest field `{key}`."})
        if self.platform_max_version and self.manifest.get("platform_max_version") != self.platform_max_version:
            raise ValidationError({"platform_max_version": "Must match manifest field `platform_max_version`."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.module_id}@{self.version}"
