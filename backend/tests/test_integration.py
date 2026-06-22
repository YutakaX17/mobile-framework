from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.audit.models import AuditEvent, AuditEventType
from apps.configurations.models import (
    ConfigurationDefinition,
    ConfigurationKind,
    ConfigurationRevision,
    ConfigurationRevisionStatus,
)
from apps.core.events import DomainEvent, EventBus
from apps.core.services import BaseService, ServiceContext, ServiceResult
from apps.form_builder.models import FormSubmission
from apps.modules.models import ModuleRegistration
from apps.sync.models import OutboxBatch, SubmissionSyncResult, SyncDevice, SyncSubmissionStatus
from apps.tenants.models import Tenant


ROOT = Path(__file__).resolve().parents[2]
VALID_MODULE_MANIFEST = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "module-manifest-core.json"
VALID_THEME = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "theme-basic.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class BackendKernelIntegrationTests(TestCase):
    def test_health_endpoint_is_routed_through_root_urlconf(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_tenant_module_and_configuration_registry_flow(self):
        tenant = Tenant.objects.create(slug="field", name="Field Operations")
        module = ModuleRegistration.from_manifest(load_json(VALID_MODULE_MANIFEST))
        module.save()
        definition = ConfigurationDefinition.objects.create(
            tenant=tenant,
            kind=ConfigurationKind.THEME,
            key="field-theme",
            name="Field Theme",
        )

        revision = ConfigurationRevision.create_next(
            definition,
            load_json(VALID_THEME),
            status=ConfigurationRevisionStatus.VALIDATED,
        )
        definition.current_revision = revision
        definition.save()

        self.assertEqual(module.module_id, "core")
        self.assertEqual(revision.revision, 1)
        self.assertEqual(definition.current_revision, revision)
        self.assertEqual(str(revision), "field:theme:field-theme#1")

    def test_service_event_and_audit_flow_share_context(self):
        tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        definition = ConfigurationDefinition.objects.create(
            tenant=tenant,
            kind=ConfigurationKind.THEME,
            key="mobile-theme",
            name="Mobile Theme",
        )
        bus = EventBus()
        observed_events = []
        bus.subscribe("configuration.published", lambda event: observed_events.append(event))

        class PublishThemeService(BaseService[dict, ConfigurationRevision]):
            def execute(self, payload: dict, context: ServiceContext) -> ConfigurationRevision:
                revision = ConfigurationRevision.create_next(
                    definition,
                    payload,
                    status=ConfigurationRevisionStatus.PUBLISHED,
                )
                definition.current_revision = revision
                definition.save()
                return revision

            def after_execute(
                self,
                input_data: dict,
                result: ServiceResult[ConfigurationRevision],
                context: ServiceContext,
            ) -> None:
                bus.dispatch(
                    DomainEvent(
                        name="configuration.published",
                        payload={
                            "definition_id": definition.id,
                            "revision": result.value.revision,
                        },
                        tenant=context.tenant,
                        request_id=context.request_id,
                        correlation_id=context.correlation_id,
                    )
                )

            def audit(
                self,
                input_data: dict,
                result: ServiceResult[ConfigurationRevision],
                context: ServiceContext,
            ) -> None:
                AuditEvent.objects.create(
                    tenant=context.tenant,
                    event_type=AuditEventType.CONFIGURATION,
                    action="configuration-published",
                    target_type="configuration_revision",
                    target_id=str(result.value.id),
                    target_repr=str(result.value),
                    request_id=context.request_id,
                    correlation_id=context.correlation_id,
                    metadata={"revision": result.value.revision},
                )

        result = PublishThemeService().run(
            load_json(VALID_THEME),
            ServiceContext(
                tenant=tenant,
                request_id="req-123",
                correlation_id="corr-123",
            ),
        )

        audit_event = AuditEvent.objects.get()
        self.assertEqual(result.value.status, ConfigurationRevisionStatus.PUBLISHED)
        self.assertEqual(definition.current_revision, result.value)
        self.assertEqual(len(observed_events), 1)
        self.assertEqual(observed_events[0].tenant, tenant)
        self.assertEqual(observed_events[0].request_id, "req-123")
        self.assertEqual(audit_event.tenant, tenant)
        self.assertEqual(audit_event.action, "configuration-published")
        self.assertEqual(audit_event.request_id, "req-123")
        self.assertEqual(audit_event.metadata, {"revision": 1})


class PracticalMvpBuilderIntegrationTests(TestCase):
    def setUp(self):
        call_command("seed_demo_mvp", verbosity=0)

    def api_headers(self) -> dict:
        return {"HTTP_X_TENANT_SLUG": "demo"}

    def publish_draft(self, kind: str, object_id: str, revision: int):
        return self.client.post(
            f"/api/{kind}/{object_id}/revisions/{revision}/publish/",
            **self.api_headers(),
        )

    def test_practical_mvp_smoke_path_from_admin_publish_to_mobile_sync(self):
        login_response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "demo-admin", "password": "demo-admin-password"}),
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["user"]["username"], "demo-admin")

        tenants_response = self.client.get("/api/auth/tenants/")
        self.assertEqual(tenants_response.status_code, 200)
        self.assertEqual(tenants_response.json()["tenants"][0]["tenant"]["slug"], "demo")

        plugin_response = self.client.get("/api/modules/field_ops/", **self.api_headers())
        self.assertEqual(plugin_response.status_code, 200)
        self.assertEqual(plugin_response.json()["module"]["status"], "enabled")

        theme_response = self.client.get("/api/themes/field_ops/", **self.api_headers())
        self.assertEqual(theme_response.status_code, 200)
        theme_payload = deepcopy(theme_response.json()["theme"]["current_revision"]["payload"])
        theme_payload["name"] = "Field Operations MVP"
        theme_payload["version"] = "0.1.1"
        theme_update = self.client.put(
            "/api/themes/field_ops/",
            data=json.dumps(theme_payload),
            content_type="application/json",
            **self.api_headers(),
        )
        self.assertEqual(theme_update.status_code, 200)
        theme_publish = self.publish_draft("themes", "field_ops", theme_update.json()["draft_revision"]["revision"])
        self.assertEqual(theme_publish.status_code, 200)
        self.assertEqual(theme_publish.json()["theme"]["current_revision"]["payload"]["version"], "0.1.1")

        form_response = self.client.get("/api/forms/patient_intake/", **self.api_headers())
        self.assertEqual(form_response.status_code, 200)
        form_payload = deepcopy(form_response.json()["form"]["current_revision"]["payload"])
        form_payload["description"] = "MVP patient intake form."
        form_payload["version"] = "0.1.1"
        form_update = self.client.put(
            "/api/forms/patient_intake/",
            data=json.dumps(form_payload),
            content_type="application/json",
            **self.api_headers(),
        )
        self.assertEqual(form_update.status_code, 200)
        form_publish = self.publish_draft("forms", "patient_intake", form_update.json()["draft_revision"]["revision"])
        self.assertEqual(form_publish.status_code, 200)
        self.assertEqual(form_publish.json()["form"]["current_revision"]["payload"]["version"], "0.1.1")

        app_response = self.client.get("/api/apps/field_ops_app/", **self.api_headers())
        self.assertEqual(app_response.status_code, 200)
        app_payload = deepcopy(app_response.json()["app"]["current_revision"]["payload"])
        app_payload["version"] = "0.1.1"
        app_payload["navigation"][0]["label"] = "MVP Intake"
        app_update = self.client.put(
            "/api/apps/field_ops_app/",
            data=json.dumps(app_payload),
            content_type="application/json",
            **self.api_headers(),
        )
        self.assertEqual(app_update.status_code, 200)
        app_publish = self.publish_draft("apps", "field_ops_app", app_update.json()["draft_revision"]["revision"])
        self.assertEqual(app_publish.status_code, 200)
        self.assertEqual(app_publish.json()["app"]["current_revision"]["payload"]["version"], "0.1.1")

        compile_response = self.client.post(
            "/api/deployment-packages/compile/",
            data=json.dumps(
                {
                    "package_id": "pkg_demo_field_ops_002",
                    "app_id": "field_ops_app",
                    "channel": "dev",
                    "runtime_min_version": "0.1.0",
                    "runtime_max_version": "0.1.0",
                    "platform_version": "0.1.0",
                    "signing_key": "test-signing-key",
                }
            ),
            content_type="application/json",
            **self.api_headers(),
        )
        self.assertEqual(compile_response.status_code, 201)
        self.assertEqual(compile_response.json()["package"]["status"], "signed")
        self.assertEqual(compile_response.json()["package"]["payload"]["app_version"], "0.1.1")

        activate_response = self.client.post(
            "/api/deployment-packages/pkg_demo_field_ops_002/activate/",
            **self.api_headers(),
        )
        self.assertEqual(activate_response.status_code, 200)
        self.assertEqual(activate_response.json()["package"]["status"], "active")

        manifest_response = self.client.get(
            "/api/mobile/packages/manifest/",
            {"app_id": "field_ops_app", "channel": "dev"},
            **self.api_headers(),
        )
        self.assertEqual(manifest_response.status_code, 200)
        manifest = manifest_response.json()["manifest"]
        self.assertEqual(manifest["package_id"], "pkg_demo_field_ops_002")
        self.assertEqual(manifest["app_version"], "0.1.1")

        download_response = self.client.get(
            "/api/mobile/packages/pkg_demo_field_ops_002/download/",
            **self.api_headers(),
        )
        self.assertEqual(download_response.status_code, 200)
        downloaded = download_response.json()
        self.assertEqual(downloaded["manifest"]["hash"], manifest["hash"])
        self.assertEqual(downloaded["package"]["modules"][1]["module_id"], "field_ops")
        self.assertEqual(downloaded["package"]["forms"][0]["version"], "0.1.1")

        register_device_response = self.client.post(
            "/api/mobile/sync/devices/",
            data=json.dumps(
                {
                    "app_version": downloaded["package"]["app_version"],
                    "device_id": "field-tablet-smoke-1",
                    "platform": "android",
                    "runtime_version": "0.1.0",
                }
            ),
            content_type="application/json",
            **self.api_headers(),
        )
        self.assertEqual(register_device_response.status_code, 201)
        self.assertEqual(register_device_response.json()["device"]["status"], "active")

        outbox_response = self.client.post(
            "/api/mobile/sync/outbox/",
            data=json.dumps(
                {
                    "app_version": downloaded["package"]["app_version"],
                    "batch_id": "smoke-batch-001",
                    "device_id": "field-tablet-smoke-1",
                    "platform": "android",
                    "runtime_version": "0.1.0",
                    "submissions": [
                        {
                            "answers": {
                                "patient_name": "Amina Nkosi",
                                "age": 34,
                                "triage_priority": "routine",
                            },
                            "client_submission_id": "smoke-submission-001",
                            "form_id": "patient_intake",
                        }
                    ],
                }
            ),
            content_type="application/json",
            **self.api_headers(),
        )
        self.assertEqual(outbox_response.status_code, 202)
        outbox_body = outbox_response.json()
        self.assertEqual(outbox_body["batch"]["status"], "accepted")
        self.assertEqual(outbox_body["session"]["accepted_count"], 1)
        self.assertEqual(outbox_body["receipts"][0]["status"], SyncSubmissionStatus.ACCEPTED)

        status_response = self.client.get(
            "/api/mobile/sync/status/",
            {"device_id": "field-tablet-smoke-1"},
            **self.api_headers(),
        )
        self.assertEqual(status_response.status_code, 200)
        status = status_response.json()
        self.assertEqual(status["devices"][0]["device_id"], "field-tablet-smoke-1")
        self.assertEqual(status["batches"][0]["batch_id"], "smoke-batch-001")
        self.assertEqual(status["batches"][0]["results"][0]["client_submission_id"], "smoke-submission-001")
        self.assertEqual(status["batches"][0]["results"][0]["status"], SyncSubmissionStatus.ACCEPTED)

        self.assertEqual(SyncDevice.objects.filter(tenant__slug="demo", device_id="field-tablet-smoke-1").count(), 1)
        self.assertEqual(OutboxBatch.objects.filter(tenant__slug="demo", batch_id="smoke-batch-001").count(), 1)
        self.assertEqual(
            SubmissionSyncResult.objects.filter(
                tenant__slug="demo",
                client_submission_id="smoke-submission-001",
            ).count(),
            1,
        )
        submission = FormSubmission.objects.get(tenant__slug="demo", form__form_id="patient_intake")
        self.assertEqual(submission.answers["patient_name"], "Amina Nkosi")
        self.assertEqual(
            AuditEvent.objects.filter(
                tenant__slug="demo",
                event_type=AuditEventType.SYNC,
                action="sync-submission-accepted",
                metadata__client_submission_id="smoke-submission-001",
            ).count(),
            1,
        )
