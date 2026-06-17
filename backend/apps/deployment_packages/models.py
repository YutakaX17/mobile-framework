from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from apps.tenants.models import TenantScopedModel

from .services import validate_deployment_package_payload


class DeploymentPackageStatus(models.TextChoices):
    SIGNED = "signed", "Signed"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class DeploymentPackage(TenantScopedModel):
    package_id = models.SlugField(max_length=100)
    app_id = models.SlugField(max_length=80)
    app_version = models.CharField(max_length=80)
    runtime_min_version = models.CharField(max_length=80)
    runtime_max_version = models.CharField(max_length=80)
    platform_version = models.CharField(max_length=80, blank=True)
    channel = models.CharField(max_length=16, default="dev")
    status = models.CharField(
        max_length=16,
        choices=DeploymentPackageStatus.choices,
        default=DeploymentPackageStatus.SIGNED,
        db_index=True,
    )
    package_hash = models.CharField(max_length=80)
    signature = models.TextField()
    payload = models.JSONField()

    class Meta:
        ordering = ["tenant__slug", "app_id", "channel", "package_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "package_id"], name="unique_package_id_per_tenant"),
            models.UniqueConstraint(
                fields=["tenant", "app_id", "app_version", "channel"],
                name="unique_package_version_per_channel",
            ),
        ]

    @classmethod
    def from_payload(cls, tenant, payload: dict):
        return cls(
            tenant=tenant,
            package_id=payload["package_id"],
            app_id=payload["app_id"],
            app_version=payload["app_version"],
            runtime_min_version=payload["runtime_min_version"],
            runtime_max_version=payload["runtime_max_version"],
            platform_version=payload.get("platform_version", ""),
            channel=payload.get("channel", "dev"),
            package_hash=payload["hash"],
            signature=payload["signature"],
            payload=payload,
        )

    def clean(self) -> None:
        super().clean()
        validate_deployment_package_payload(self.payload)
        expected_values = {
            "tenant_id": self.tenant.slug if self.tenant_id else None,
            "package_id": self.package_id,
            "app_id": self.app_id,
            "app_version": self.app_version,
            "runtime_min_version": self.runtime_min_version,
            "runtime_max_version": self.runtime_max_version,
            "channel": self.channel,
            "hash": self.package_hash,
            "signature": self.signature,
        }
        if self.platform_version:
            expected_values["platform_version"] = self.platform_version

        for key, expected in expected_values.items():
            if expected is not None and self.payload.get(key) != expected:
                raise ValidationError({key: f"Must match payload field `{key}`."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.package_id}"
