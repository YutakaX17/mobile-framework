from django.db import IntegrityError
from django.test import TestCase

from apps.tenants.models import Tenant, TenantStatus


class TenantModelTests(TestCase):
    def test_tenant_defaults_to_active_status(self):
        tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")

        self.assertEqual(tenant.status, TenantStatus.ACTIVE)
        self.assertEqual(str(tenant), "Demo Tenant")
        self.assertIsNotNone(tenant.id)
        self.assertIsNotNone(tenant.created_at)
        self.assertIsNotNone(tenant.updated_at)

    def test_tenant_slug_is_unique(self):
        Tenant.objects.create(slug="demo", name="Demo Tenant")

        with self.assertRaises(IntegrityError):
            Tenant.objects.create(slug="demo", name="Duplicate Tenant")

    def test_tenant_can_be_suspended(self):
        tenant = Tenant.objects.create(
            slug="suspended-demo",
            name="Suspended Demo",
            status=TenantStatus.SUSPENDED,
        )

        self.assertEqual(tenant.status, TenantStatus.SUSPENDED)
