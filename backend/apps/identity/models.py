from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.tenants.models import TenantScopedModel


class PlatformPermission(models.Model):
    code = models.SlugField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class PlatformRole(TenantScopedModel):
    slug = models.SlugField(max_length=64)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        PlatformPermission,
        through="RolePermission",
        related_name="roles",
        blank=True,
    )

    class Meta:
        ordering = ["tenant__slug", "slug"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="unique_role_slug_per_tenant"),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.slug}"


class RolePermission(models.Model):
    role = models.ForeignKey(PlatformRole, on_delete=models.CASCADE)
    permission = models.ForeignKey(PlatformPermission, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="unique_permission_per_role"),
        ]

    def __str__(self) -> str:
        return f"{self.role} -> {self.permission.code}"


class UserRoleAssignment(TenantScopedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(PlatformRole, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["tenant__slug", "user_id", "role__slug"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user", "role"],
                name="unique_role_assignment_per_tenant_user",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.role_id and self.tenant_id and self.role.tenant_id != self.tenant_id:
            raise ValidationError({"role": "Assigned role must belong to the same tenant."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user_id}:{self.tenant.slug}:{self.role.slug}"
