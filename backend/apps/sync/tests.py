import json
from copy import deepcopy
from pathlib import Path

from django.test import TestCase

from apps.audit.models import AuditEvent, AuditEventType
from apps.form_builder.models import FormDefinition, FormRevision, FormRevisionStatus, FormSubmission
from apps.tenants.models import Tenant

from .models import OutboxBatch, SubmissionSyncResult, SyncBatchStatus, SyncDevice, SyncSubmissionStatus


ROOT = Path(__file__).resolve().parents[3]
VALID_FORM = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "form-patient-intake.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class MobileSyncApiTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        form_payload = load_json(VALID_FORM)
        self.form = FormDefinition.from_payload(self.tenant, form_payload)
        self.form.save()
        self.form_revision = FormRevision.create_next(
            self.form,
            deepcopy(form_payload),
            status=FormRevisionStatus.PUBLISHED,
        )
        self.form.current_revision = self.form_revision
        self.form.save()

    def headers(self, tenant_slug: str = "demo") -> dict:
        return {"HTTP_X_TENANT_SLUG": tenant_slug}

    def outbox_payload(
        self,
        *,
        batch_id: str = "batch-001",
        client_submission_id: str = "client-001",
        form_id: str = "patient_intake",
        answers: dict | None = None,
    ) -> dict:
        return {
            "app_version": "0.1.0",
            "batch_id": batch_id,
            "device_id": "field-tablet-1",
            "platform": "android",
            "runtime_version": "0.1.0",
            "submissions": [
                {
                    "answers": answers if answers is not None else {"patient_name": "Amina", "age": 34},
                    "client_submission_id": client_submission_id,
                    "form_id": form_id,
                }
            ],
        }

    def post_outbox(self, payload: dict, tenant_slug: str = "demo"):
        return self.client.post(
            "/api/mobile/sync/outbox/",
            data=json.dumps(payload),
            content_type="application/json",
            **self.headers(tenant_slug),
        )

    def test_register_device_creates_or_updates_device(self):
        response = self.client.post(
            "/api/mobile/sync/devices/",
            data=json.dumps(
                {
                    "app_version": "0.1.0",
                    "device_id": "field-tablet-1",
                    "platform": "android",
                    "runtime_version": "0.1.0",
                }
            ),
            content_type="application/json",
            **self.headers(),
        )

        self.assertEqual(response.status_code, 201)
        device = response.json()["device"]
        self.assertEqual(device["device_id"], "field-tablet-1")
        self.assertEqual(device["platform"], "android")
        self.assertEqual(SyncDevice.objects.filter(tenant=self.tenant, device_id="field-tablet-1").count(), 1)

    def test_outbox_accepts_submission_and_records_audit_event(self):
        response = self.post_outbox(self.outbox_payload())

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["batch"]["status"], SyncBatchStatus.ACCEPTED)
        self.assertEqual(body["session"]["accepted_count"], 1)
        self.assertEqual(body["receipts"][0]["status"], SyncSubmissionStatus.ACCEPTED)
        self.assertEqual(FormSubmission.objects.filter(tenant=self.tenant, form=self.form).count(), 1)
        result = SubmissionSyncResult.objects.get(client_submission_id="client-001")
        self.assertEqual(result.status, SyncSubmissionStatus.ACCEPTED)
        self.assertEqual(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                event_type=AuditEventType.SYNC,
                action="sync-submission-accepted",
            ).count(),
            1,
        )

    def test_outbox_replays_duplicate_client_submission_without_new_submission(self):
        first = self.post_outbox(self.outbox_payload(batch_id="batch-001", client_submission_id="client-dup"))
        second = self.post_outbox(self.outbox_payload(batch_id="batch-002", client_submission_id="client-dup"))

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        body = second.json()
        self.assertEqual(body["receipts"][0]["status"], SyncSubmissionStatus.DUPLICATE)
        self.assertEqual(body["session"]["duplicate_count"], 1)
        self.assertEqual(FormSubmission.objects.filter(tenant=self.tenant, form=self.form).count(), 1)
        self.assertEqual(SubmissionSyncResult.objects.filter(client_submission_id="client-dup").count(), 1)

    def test_outbox_retries_existing_batch_without_constraint_error(self):
        payload = self.outbox_payload(batch_id="batch-retry", client_submission_id="client-retry")
        first = self.post_outbox(payload)
        second = self.post_outbox(payload)

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(second.json()["batch"]["batch_id"], "batch-retry")
        self.assertEqual(OutboxBatch.objects.filter(tenant=self.tenant, batch_id="batch-retry").count(), 1)
        self.assertEqual(FormSubmission.objects.filter(tenant=self.tenant, form=self.form).count(), 1)

    def test_outbox_rejects_unknown_or_cross_tenant_form(self):
        response = self.post_outbox(
            self.outbox_payload(batch_id="batch-other", client_submission_id="client-other"),
            tenant_slug="other",
        )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["batch"]["status"], SyncBatchStatus.REJECTED)
        self.assertEqual(body["receipts"][0]["status"], SyncSubmissionStatus.REJECTED)
        self.assertEqual(body["receipts"][0]["reason_code"], "unknown_form")
        self.assertEqual(FormSubmission.objects.count(), 0)
        self.assertEqual(
            AuditEvent.objects.filter(
                tenant=self.other_tenant,
                event_type=AuditEventType.SYNC,
                action="sync-submission-rejected",
            ).count(),
            1,
        )

    def test_outbox_rejects_invalid_answers(self):
        response = self.post_outbox(
            self.outbox_payload(batch_id="batch-invalid", client_submission_id="client-invalid", answers=["bad"])
        )

        self.assertEqual(response.status_code, 202)
        receipt = response.json()["receipts"][0]
        self.assertEqual(receipt["status"], SyncSubmissionStatus.REJECTED)
        self.assertEqual(receipt["reason_code"], "invalid_answers")
        self.assertEqual(SubmissionSyncResult.objects.get(client_submission_id="client-invalid").status, SyncSubmissionStatus.REJECTED)

    def test_sync_status_returns_device_batches_and_results(self):
        self.post_outbox(self.outbox_payload(batch_id="batch-status", client_submission_id="client-status"))

        response = self.client.get(
            "/api/mobile/sync/status/",
            {"device_id": "field-tablet-1"},
            **self.headers(),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["devices"][0]["device_id"], "field-tablet-1")
        self.assertEqual(body["batches"][0]["batch_id"], "batch-status")
        self.assertEqual(body["batches"][0]["results"][0]["client_submission_id"], "client-status")

    def test_sync_endpoints_require_tenant(self):
        response = self.client.get("/api/mobile/sync/status/")

        self.assertEqual(response.status_code, 400)

    def test_sync_endpoints_reject_wrong_method(self):
        response = self.client.get("/api/mobile/sync/outbox/", **self.headers())

        self.assertEqual(response.status_code, 405)
