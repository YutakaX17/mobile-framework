import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.app_builder.models import AppDefinition, AppRevision, AppRevisionStatus
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
