import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.form_builder.models import FormDefinition, FormRevision, FormRevisionStatus
from apps.tenants.models import Tenant


ROOT = Path(__file__).resolve().parents[3]
VALID_FORM = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "form-patient-intake.json"


def load_valid_form() -> dict:
    with VALID_FORM.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class FormRegistryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.payload = load_valid_form()
        self.form = FormDefinition.from_payload(self.tenant, self.payload)
        self.form.save()

    def test_form_can_be_created_from_valid_payload(self):
        self.assertEqual(self.form.form_id, "patient_intake")
        self.assertEqual(self.form.name, "Patient Intake")
        self.assertEqual(self.form.mode, "standalone")
        self.assertEqual(str(self.form), "demo:patient_intake")

    def test_valid_form_revision_is_created(self):
        revision = FormRevision.create_next(
            self.form,
            deepcopy(self.payload),
            status=FormRevisionStatus.REVIEWED,
        )

        self.assertEqual(revision.revision, 1)
        self.assertEqual(revision.version, "0.1.0")
        self.assertEqual(revision.schema_version, "v1")
        self.assertEqual(revision.status, FormRevisionStatus.REVIEWED)
        self.assertEqual(str(revision), "demo:patient_intake#1")

    def test_invalid_form_payload_is_rejected(self):
        payload = deepcopy(self.payload)
        payload.pop("fields")

        with self.assertRaises(ValidationError):
            FormRevision.create_next(self.form, payload)

    def test_form_id_is_unique_per_tenant(self):
        with self.assertRaises(ValidationError):
            FormDefinition.from_payload(self.tenant, self.payload).save()

        other_tenant_form = FormDefinition.from_payload(self.other_tenant, self.payload)
        other_tenant_form.save()

        self.assertEqual(other_tenant_form.form_id, "patient_intake")

    def test_revision_numbering_increments_per_form(self):
        first = FormRevision.create_next(self.form, deepcopy(self.payload))
        second = FormRevision.create_next(self.form, deepcopy(self.payload))

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)

    def test_revision_fields_must_match_payload(self):
        payload = deepcopy(self.payload)
        payload["form_id"] = "other_form"

        with self.assertRaises(ValidationError):
            FormRevision.create_next(self.form, payload)

    def test_current_revision_must_belong_to_form(self):
        revision = FormRevision.create_next(self.form, deepcopy(self.payload))
        other_payload = deepcopy(self.payload)
        other_payload["form_id"] = "other_form"
        other_payload["name"] = "Other Form"
        other_form = FormDefinition.from_payload(self.tenant, other_payload)
        other_form.save()

        other_form.current_revision = revision

        with self.assertRaises(ValidationError):
            other_form.full_clean()

    def test_revision_tenant_must_match_form_tenant(self):
        revision = FormRevision(
            tenant=self.other_tenant,
            form=self.form,
            revision=1,
            version=self.payload["version"],
            payload=deepcopy(self.payload),
        )

        with self.assertRaises(ValidationError):
            revision.full_clean()


class FormApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.payload = load_valid_form()
        self.form = FormDefinition.from_payload(self.tenant, self.payload)
        self.form.save()
        self.revision = FormRevision.create_next(
            self.form,
            deepcopy(self.payload),
            status=FormRevisionStatus.PUBLISHED,
        )
        self.form.current_revision = self.revision
        self.form.save()

    def test_form_list_returns_tenant_form_summaries(self):
        response = self.client.get("/api/forms/", {"tenant": "demo"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["forms"][0]["form_id"], "patient_intake")
        self.assertEqual(payload["forms"][0]["current_revision"]["status"], FormRevisionStatus.PUBLISHED)
        self.assertEqual(payload["forms"][0]["current_revision"]["field_count"], 3)
        self.assertNotIn("payload", payload["forms"][0]["current_revision"])

    def test_form_detail_returns_current_revision_payload(self):
        response = self.client.get("/api/forms/patient_intake/", {"tenant": "demo"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["form"]["form_id"], "patient_intake")
        self.assertEqual(payload["form"]["current_revision"]["payload"]["form_id"], "patient_intake")

    def test_form_api_requires_tenant_query_parameter(self):
        response = self.client.get("/api/forms/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_form_api_returns_not_found_for_missing_tenant(self):
        response = self.client.get("/api/forms/", {"tenant": "missing"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_form_detail_returns_not_found_for_missing_form(self):
        response = self.client.get("/api/forms/missing_form/", {"tenant": "demo"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")
