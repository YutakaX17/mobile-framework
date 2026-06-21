import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase

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


class IdentitySessionApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.user = get_user_model().objects.create_user(
            username="demo-admin",
            email="demo-admin@example.com",
            password="demo-admin-password",
        )
        permission = PlatformPermission.objects.create(code="builder.app.manage", name="Manage apps")
        self.role = PlatformRole.objects.create(tenant=self.tenant, slug="admin", name="Administrator")
        RolePermission.objects.create(role=self.role, permission=permission)
        UserRoleAssignment.objects.create(tenant=self.tenant, user=self.user, role=self.role)

    def test_login_session_and_logout_flow(self):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "demo-admin", "password": "demo-admin-password"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], "demo-admin")

        session_response = self.client.get("/api/auth/session/")
        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response.json()["user"]["username"], "demo-admin")

        logout_response = self.client.post("/api/auth/logout/")
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/session/").status_code, 401)

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "demo-admin", "password": "wrong"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_tenant_list_requires_authentication(self):
        response = self.client.get("/api/auth/tenants/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_tenant_list_returns_user_assignments(self):
        self.client.force_login(self.user)

        response = self.client.get("/api/auth/tenants/")

        self.assertEqual(response.status_code, 200)
        tenants = response.json()["tenants"]
        self.assertEqual(len(tenants), 1)
        self.assertEqual(tenants[0]["tenant"]["slug"], "demo")
        self.assertEqual(tenants[0]["permissions"], ["builder.app.manage"])

    def test_current_tenant_prefers_header(self):
        self.client.force_login(self.user)

        response = self.client.get("/api/auth/tenant/?tenant=other", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tenant"]["slug"], "demo")
        self.assertEqual(response.json()["source"], "header")

    def test_current_tenant_keeps_query_fallback_for_development(self):
        self.client.force_login(self.user)

        response = self.client.get("/api/auth/tenant/?tenant=demo")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tenant"]["slug"], "demo")
        self.assertEqual(response.json()["source"], "query")

    def test_current_tenant_rejects_wrong_tenant(self):
        self.client.force_login(self.user)

        response = self.client.get("/api/auth/tenant/", HTTP_X_TENANT_SLUG="other")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")

    def test_csrf_cookie_allows_session_login_when_csrf_checks_are_enforced(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_response = csrf_client.get("/api/auth/csrf/")
        token = csrf_response.cookies["csrftoken"].value

        response = csrf_client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "demo-admin", "password": "demo-admin-password"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], "demo-admin")
