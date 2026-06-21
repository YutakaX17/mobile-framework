import json
from copy import deepcopy
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.form_builder.models import FormDefinition, FormRevision, FormRevisionStatus, FormSubmission, FormSubmissionStatus
from apps.identity.models import PlatformPermission, PlatformRole, RolePermission, UserRoleAssignment
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
        self.user = get_user_model().objects.create_user(username="form-builder")
        self.grant_permissions(self.user, self.tenant, ["builder.form.manage", "builder.package.publish"])
        self.client.force_login(self.user)
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

    def grant_permissions(self, user, tenant, permission_codes: list[str]) -> PlatformRole:
        role = PlatformRole.objects.create(tenant=tenant, slug=f"role-{user.username}", name="Form Builder")
        for code in permission_codes:
            permission, _created = PlatformPermission.objects.get_or_create(code=code, defaults={"name": code})
            RolePermission.objects.create(role=role, permission=permission)
        UserRoleAssignment.objects.create(tenant=tenant, user=user, role=role)
        return role

    def test_form_api_requires_authentication(self):
        response = Client().get("/api/forms/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_form_api_rejects_missing_permission(self):
        user = get_user_model().objects.create_user(username="form-viewer")
        self.grant_permissions(user, self.tenant, ["core.view_dashboard"])
        client = Client()
        client.force_login(user)

        response = client.get("/api/forms/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")

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

    def test_update_form_creates_draft_revision(self):
        updated_payload = deepcopy(self.payload)
        updated_payload["name"] = "Patient Intake Draft"
        updated_payload["description"] = "Updated form draft."
        updated_payload["version"] = "0.2.0"

        response = self.client.put(
            "/api/forms/patient_intake/?tenant=demo",
            data=json.dumps(updated_payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["form"]["name"], "Patient Intake Draft")
        self.assertEqual(payload["form"]["current_revision"]["revision"], self.revision.revision)
        self.assertEqual(payload["draft_revision"]["revision"], 2)
        self.assertEqual(payload["draft_revision"]["status"], FormRevisionStatus.DRAFT)
        self.assertEqual(payload["draft_revision"]["payload"]["version"], "0.2.0")

        self.form.refresh_from_db()
        self.revision.refresh_from_db()
        draft_revision = self.form.revisions.get(revision=2)
        self.assertEqual(self.form.current_revision_id, self.revision.id)
        self.assertEqual(self.revision.status, FormRevisionStatus.PUBLISHED)
        self.assertEqual(draft_revision.status, FormRevisionStatus.DRAFT)

    def test_update_form_rejects_invalid_payload(self):
        invalid_payload = deepcopy(self.payload)
        invalid_payload.pop("fields")

        response = self.client.put(
            "/api/forms/patient_intake/?tenant=demo",
            data=json.dumps(invalid_payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "validation_error")
        self.assertEqual(self.form.revisions.count(), 1)

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

    def test_publish_revision_sets_current_revision(self):
        next_revision = FormRevision.create_next(
            self.form,
            deepcopy(self.payload),
            status=FormRevisionStatus.REVIEWED,
        )

        response = self.client.post(
            f"/api/forms/patient_intake/revisions/{next_revision.revision}/publish/?tenant=demo",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["form"]["current_revision"]["revision"], next_revision.revision)
        next_revision.refresh_from_db()
        self.revision.refresh_from_db()
        self.form.refresh_from_db()
        self.assertEqual(next_revision.status, FormRevisionStatus.PUBLISHED)
        self.assertEqual(self.revision.status, FormRevisionStatus.ARCHIVED)
        self.assertEqual(self.form.current_revision_id, next_revision.id)

    def test_publish_revision_returns_not_found_for_missing_revision(self):
        response = self.client.post("/api/forms/patient_intake/revisions/99/publish/?tenant=demo")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_form_submit_creates_submission_for_current_revision(self):
        response = self.client.post(
            "/api/forms/patient_intake/submissions/?tenant=demo",
            data=json.dumps({"answers": {"age": 36, "full_name": "Ada Lovelace"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()["submission"]
        self.assertEqual(payload["form_id"], "patient_intake")
        self.assertEqual(payload["revision"], self.revision.revision)
        self.assertEqual(payload["status"], FormSubmissionStatus.RECEIVED)
        self.assertEqual(payload["answer_count"], 2)

        submission = FormSubmission.objects.get(id=payload["id"])
        self.assertEqual(submission.tenant, self.tenant)
        self.assertEqual(submission.form, self.form)
        self.assertEqual(submission.revision, self.revision)
        self.assertEqual(submission.answers["full_name"], "Ada Lovelace")

    def test_form_submit_is_tenant_scoped(self):
        other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        other_form = FormDefinition.from_payload(other_tenant, self.payload)
        other_form.save()
        other_revision = FormRevision.create_next(
            other_form,
            deepcopy(self.payload),
            status=FormRevisionStatus.PUBLISHED,
        )
        other_form.current_revision = other_revision
        other_form.save()

        response = self.client.post(
            "/api/forms/patient_intake/submissions/?tenant=other",
            data=json.dumps({"answers": {"full_name": "Grace Hopper"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        submission = FormSubmission.objects.get(id=response.json()["submission"]["id"])
        self.assertEqual(submission.tenant, other_tenant)
        self.assertEqual(submission.form, other_form)
        self.assertEqual(submission.revision, other_revision)
        self.assertEqual(FormSubmission.objects.filter(tenant=self.tenant).count(), 0)

    def test_form_submit_returns_not_found_for_missing_form(self):
        response = self.client.post(
            "/api/forms/missing_form/submissions/?tenant=demo",
            data=json.dumps({"answers": {"full_name": "Ada Lovelace"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_form_submit_returns_conflict_without_current_revision(self):
        self.form.current_revision = None
        self.form.save()

        response = self.client.post(
            "/api/forms/patient_intake/submissions/?tenant=demo",
            data=json.dumps({"answers": {"full_name": "Ada Lovelace"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "conflict")
        self.assertEqual(FormSubmission.objects.count(), 0)

    def test_form_submit_rejects_invalid_body(self):
        response = self.client.post(
            "/api/forms/patient_intake/submissions/?tenant=demo",
            data=json.dumps({"answers": []}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "validation_error")
        self.assertEqual(response.json()["error"]["details"][0]["field"], "answers")
        self.assertEqual(FormSubmission.objects.count(), 0)
