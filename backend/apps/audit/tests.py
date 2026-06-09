from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.audit.models import AuditEvent, AuditEventType, AuditSeverity
from apps.tenants.models import Tenant


class AuditEventModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.user = get_user_model().objects.create_user(username="auditor")

    def test_tenant_scoped_event_can_be_recorded(self):
        event = AuditEvent.objects.create(
            tenant=self.tenant,
            actor=self.user,
            event_type=AuditEventType.CONFIGURATION,
            severity=AuditSeverity.INFO,
            action="configuration-published",
            target_type="configuration_revision",
            target_id="42",
            request_id="req-123",
            correlation_id="corr-123",
            ip_address="127.0.0.1",
            metadata={"revision": 3},
        )

        self.assertEqual(event.scope, "demo")
        self.assertEqual(str(event), "demo:configuration:configuration-published")
        self.assertEqual(event.metadata["revision"], 3)

    def test_platform_event_can_be_recorded_without_tenant(self):
        event = AuditEvent.objects.create(
            event_type=AuditEventType.SYSTEM,
            severity=AuditSeverity.WARNING,
            action="maintenance-started",
            metadata={"window": "planned"},
        )

        self.assertIsNone(event.tenant)
        self.assertEqual(event.scope, "platform")
        self.assertEqual(str(event), "platform:system:maintenance-started")

    def test_action_is_required(self):
        event = AuditEvent(
            event_type=AuditEventType.SECURITY,
            severity=AuditSeverity.CRITICAL,
            action="",
        )

        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_event_type_and_severity_are_constrained(self):
        event = AuditEvent(event_type="unknown", severity="minor", action="bad-event")

        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_metadata_must_be_json_object(self):
        event = AuditEvent(
            tenant=self.tenant,
            event_type=AuditEventType.IDENTITY,
            severity=AuditSeverity.ERROR,
            action="role-assignment-failed",
            metadata=["not", "an", "object"],
        )

        with self.assertRaises(ValidationError):
            event.full_clean()
