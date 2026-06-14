from __future__ import annotations

import json
from pathlib import Path

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
from apps.modules.models import ModuleRegistration
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
