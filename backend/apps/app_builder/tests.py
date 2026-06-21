import json
from copy import deepcopy
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.app_builder.models import AppDefinition, AppRevision, AppRevisionStatus
from apps.identity.models import PlatformPermission, PlatformRole, RolePermission, UserRoleAssignment
from apps.tenants.models import Tenant


ROOT = Path(__file__).resolve().parents[3]
VALID_APP = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "app-field-ops.json"


def load_valid_app() -> dict:
    with VALID_APP.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class AppRegistryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.payload = load_valid_app()
        self.app = AppDefinition.from_payload(self.tenant, self.payload)
        self.app.save()

    def test_app_can_be_created_from_valid_payload(self):
        self.assertEqual(self.app.app_id, "field_ops_app")
        self.assertEqual(self.app.name, "Field Operations")
        self.assertEqual(self.app.description, "Mobile field operations starter app.")
        self.assertEqual(str(self.app), "demo:field_ops_app")

    def test_valid_app_revision_is_created(self):
        revision = AppRevision.create_next(
            self.app,
            deepcopy(self.payload),
            status=AppRevisionStatus.REVIEWED,
        )

        self.assertEqual(revision.revision, 1)
        self.assertEqual(revision.version, "0.1.0")
        self.assertEqual(revision.schema_version, "v1")
        self.assertEqual(revision.status, AppRevisionStatus.REVIEWED)
        self.assertEqual(str(revision), "demo:field_ops_app#1")

    def test_invalid_app_payload_is_rejected(self):
        payload = deepcopy(self.payload)
        payload.pop("navigation")

        with self.assertRaises(ValidationError):
            AppRevision.create_next(self.app, payload)

    def test_app_id_is_unique_per_tenant(self):
        with self.assertRaises(ValidationError):
            AppDefinition.from_payload(self.tenant, self.payload).save()

        other_tenant_app = AppDefinition.from_payload(self.other_tenant, self.payload)
        other_tenant_app.save()

        self.assertEqual(other_tenant_app.app_id, "field_ops_app")

    def test_revision_numbering_increments_per_app(self):
        first = AppRevision.create_next(self.app, deepcopy(self.payload))
        second = AppRevision.create_next(self.app, deepcopy(self.payload))

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)

    def test_revision_fields_must_match_payload(self):
        payload = deepcopy(self.payload)
        payload["app_id"] = "other_app"

        with self.assertRaises(ValidationError):
            AppRevision.create_next(self.app, payload)

    def test_current_revision_must_belong_to_app(self):
        revision = AppRevision.create_next(self.app, deepcopy(self.payload))
        other_payload = deepcopy(self.payload)
        other_payload["app_id"] = "other_app"
        other_payload["name"] = "Other App"
        other_app = AppDefinition.from_payload(self.tenant, other_payload)
        other_app.save()

        other_app.current_revision = revision

        with self.assertRaises(ValidationError):
            other_app.full_clean()

    def test_revision_tenant_must_match_app_tenant(self):
        revision = AppRevision(
            tenant=self.other_tenant,
            app=self.app,
            revision=1,
            version=self.payload["version"],
            payload=deepcopy(self.payload),
        )

        with self.assertRaises(ValidationError):
            revision.full_clean()


class AppApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.user = get_user_model().objects.create_user(username="app-builder")
        self.grant_permissions(self.user, self.tenant, ["builder.app.manage"])
        self.client.force_login(self.user)
        self.payload = load_valid_app()
        self.app = AppDefinition.from_payload(self.tenant, self.payload)
        self.app.save()
        self.revision = AppRevision.create_next(
            self.app,
            deepcopy(self.payload),
            status=AppRevisionStatus.PUBLISHED,
        )
        self.app.current_revision = self.revision
        self.app.save()

    def grant_permissions(self, user, tenant, permission_codes: list[str]) -> PlatformRole:
        role = PlatformRole.objects.create(tenant=tenant, slug=f"role-{user.username}", name="App Builder")
        for code in permission_codes:
            permission, _created = PlatformPermission.objects.get_or_create(code=code, defaults={"name": code})
            RolePermission.objects.create(role=role, permission=permission)
        UserRoleAssignment.objects.create(tenant=tenant, user=user, role=role)
        return role

    def test_app_api_requires_authentication(self):
        response = Client().get("/api/apps/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_app_api_rejects_wrong_tenant(self):
        response = self.client.get("/api/apps/", HTTP_X_TENANT_SLUG="other")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")

    def test_app_api_rejects_missing_permission(self):
        user = get_user_model().objects.create_user(username="app-viewer")
        self.grant_permissions(user, self.tenant, ["core.view_dashboard"])
        client = Client()
        client.force_login(user)

        response = client.get("/api/apps/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")

    def test_app_list_returns_tenant_app_summaries(self):
        response = self.client.get("/api/apps/", {"tenant": "demo"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["apps"][0]["app_id"], "field_ops_app")
        self.assertEqual(payload["apps"][0]["current_revision"]["status"], AppRevisionStatus.PUBLISHED)
        self.assertEqual(payload["apps"][0]["current_revision"]["navigation_count"], 1)
        self.assertEqual(payload["apps"][0]["current_revision"]["screen_count"], 1)
        self.assertEqual(payload["apps"][0]["current_revision"]["permission_count"], 1)
        self.assertNotIn("payload", payload["apps"][0]["current_revision"])

    def test_app_detail_returns_current_revision_payload(self):
        response = self.client.get("/api/apps/field_ops_app/", {"tenant": "demo"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["app"]["app_id"], "field_ops_app")
        self.assertEqual(payload["app"]["current_revision"]["payload"]["app_id"], "field_ops_app")

    def test_app_api_requires_tenant_query_parameter(self):
        response = self.client.get("/api/apps/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_app_api_returns_not_found_for_missing_tenant(self):
        response = self.client.get("/api/apps/", {"tenant": "missing"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_app_detail_returns_not_found_for_missing_app(self):
        response = self.client.get("/api/apps/missing_app/", {"tenant": "demo"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_publish_revision_sets_current_revision(self):
        next_revision = AppRevision.create_next(
            self.app,
            deepcopy(self.payload),
            status=AppRevisionStatus.REVIEWED,
        )

        response = self.client.post(
            f"/api/apps/field_ops_app/revisions/{next_revision.revision}/publish/?tenant=demo",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["app"]["current_revision"]["revision"], next_revision.revision)
        next_revision.refresh_from_db()
        self.revision.refresh_from_db()
        self.app.refresh_from_db()
        self.assertEqual(next_revision.status, AppRevisionStatus.PUBLISHED)
        self.assertEqual(self.revision.status, AppRevisionStatus.ARCHIVED)
        self.assertEqual(self.app.current_revision_id, next_revision.id)

    def test_publish_revision_returns_not_found_for_missing_revision(self):
        response = self.client.post("/api/apps/field_ops_app/revisions/99/publish/?tenant=demo")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_publish_revision_returns_not_found_for_missing_app(self):
        response = self.client.post("/api/apps/missing_app/revisions/1/publish/?tenant=demo")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")
