from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.tenants.models import Tenant


class AuditEventType(models.TextChoices):
    CONFIGURATION = "configuration", "Configuration"
    DEPLOYMENT = "deployment", "Deployment"
    IDENTITY = "identity", "Identity"
    MODULE = "module", "Module"
    SECURITY = "security", "Security"
    SYNC = "sync", "Sync"
    SYSTEM = "system", "System"


class AuditSeverity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"
    CRITICAL = "critical", "Critical"


class AuditEvent(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.PROTECT, related_name="audit_events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    event_type = models.CharField(max_length=32, choices=AuditEventType.choices, db_index=True)
    severity = models.CharField(max_length=16, choices=AuditSeverity.choices, default=AuditSeverity.INFO, db_index=True)
    action = models.SlugField(max_length=128)
    target_type = models.CharField(max_length=128, blank=True)
    target_id = models.CharField(max_length=128, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    request_id = models.CharField(max_length=128, blank=True, db_index=True)
    correlation_id = models.CharField(max_length=128, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["tenant", "event_type", "occurred_at"], name="audit_tenant_event_time_idx"),
            models.Index(fields=["action", "occurred_at"], name="audit_action_time_idx"),
        ]

    @property
    def scope(self) -> str:
        return self.tenant.slug if self.tenant_id else "platform"

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": "Audit metadata must be a JSON object."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.scope}:{self.event_type}:{self.action}"
