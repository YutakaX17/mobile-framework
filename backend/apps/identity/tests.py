from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.identity.models import (
    PlatformPermission,
    PlatformRole,
    RolePermission,
    UserRoleAssignment,
)
from apps.tenants.models import Tenant


class IdentityRbacModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.user = get_user_model().objects.create_user(username="builder")

    def test_role_and_permission_can_be_linked(self):
        role = PlatformRole.objects.create(tenant=self.tenant, slug="admin", name="Administrator")
        permission = PlatformPermission.objects.create(code="builder.publish", name="Publish package")

        link = RolePermission.objects.create(role=role, permission=permission)

        self.assertEqual(str(role), "demo:admin")
        self.assertEqual(str(permission), "builder.publish")
        self.assertEqual(str(link), "demo:admin -> builder.publish")
        self.assertEqual(list(role.permissions.all()), [permission])

    def test_role_slug_is_unique_per_tenant(self):
        PlatformRole.objects.create(tenant=self.tenant, slug="admin", name="Administrator")

        with self.assertRaises(IntegrityError), transaction.atomic():
            PlatformRole.objects.create(tenant=self.tenant, slug="admin", name="Duplicate")

        role = PlatformRole.objects.create(
            tenant=self.other_tenant,
            slug="admin",
            name="Other Administrator",
        )

        self.assertEqual(role.slug, "admin")

    def test_permission_code_is_unique(self):
        PlatformPermission.objects.create(code="builder.publish", name="Publish package")

        with self.assertRaises(IntegrityError), transaction.atomic():
            PlatformPermission.objects.create(code="builder.publish", name="Duplicate")

    def test_assignment_requires_role_from_same_tenant(self):
        role = PlatformRole.objects.create(
            tenant=self.other_tenant,
            slug="admin",
            name="Other Administrator",
        )

        assignment = UserRoleAssignment(tenant=self.tenant, user=self.user, role=role)

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_assignment_is_unique_per_tenant_user_and_role(self):
        role = PlatformRole.objects.create(tenant=self.tenant, slug="admin", name="Administrator")
        UserRoleAssignment.objects.create(tenant=self.tenant, user=self.user, role=role)

        with self.assertRaises(ValidationError):
            UserRoleAssignment.objects.create(tenant=self.tenant, user=self.user, role=role)
