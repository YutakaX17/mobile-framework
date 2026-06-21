from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.app_builder.models import AppDefinition, AppRevision, AppRevisionStatus
from apps.audit.models import AuditEvent
from apps.core.errors import ApiError, ApiErrorCode, ApiErrorDetail, api_error_response
from apps.core.events import DomainEvent, EventBus
from apps.core.jobs import BackgroundJob, BackgroundJobRegistry, BackgroundJobResult, BackgroundJobStatus
from apps.core.services import BaseService, ServiceContext, ServiceResult
from apps.deployment_packages.models import DeploymentChannel, DeploymentPackage, DeploymentPackageStatus
from apps.deployment_packages.services import release_channel_names, verify_deployment_package_hash
from apps.form_builder.models import FormDefinition, FormRevision, FormRevisionStatus
from apps.identity.models import PlatformPermission, PlatformRole, RolePermission, UserRoleAssignment
from apps.modules.models import ModuleRegistration, ModuleRegistrationStatus
from apps.tenants.models import Tenant, TenantStatus
from apps.themes.models import Theme, ThemeRevision, ThemeRevisionStatus


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class SeedDemoMvpCommandTests(TestCase):
    def run_seed(self) -> str:
        output = StringIO()
        call_command("seed_demo_mvp", stdout=output)
        return output.getvalue()

    def test_seed_demo_mvp_can_run_twice_safely(self):
        first_output = self.run_seed()
        second_output = self.run_seed()

        tenant = Tenant.objects.get(slug="demo")
        admin = get_user_model().objects.get(username="demo-admin")
        theme = Theme.objects.get(tenant=tenant, theme_id="field_ops")
        form = FormDefinition.objects.get(tenant=tenant, form_id="patient_intake")
        app = AppDefinition.objects.get(tenant=tenant, app_id="field_ops_app")
        package = DeploymentPackage.objects.get(tenant=tenant, package_id="pkg_demo_field_ops_001")

        self.assertIn("Seeded demo MVP tenant `demo`", first_output)
        self.assertIn("Field Ops plugin", second_output)
        self.assertEqual(tenant.name, "Demo Tenant")
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("demo-admin-password"))

        self.assertEqual(PlatformPermission.objects.count(), 8)
        self.assertEqual(PlatformRole.objects.filter(tenant=tenant).count(), 3)
        self.assertEqual(RolePermission.objects.count(), 16)
        self.assertEqual(UserRoleAssignment.objects.filter(tenant=tenant, user=admin).count(), 1)
        self.assertEqual(
            set(DeploymentChannel.objects.filter(tenant=tenant).values_list("channel", flat=True)),
            set(release_channel_names()),
        )

        self.assertEqual(ModuleRegistration.objects.count(), 2)
        core_module = ModuleRegistration.objects.get(module_id="core", version="0.1.0")
        field_ops_module = ModuleRegistration.objects.get(module_id="field_ops", version="0.1.0")
        self.assertEqual(core_module.status, ModuleRegistrationStatus.ENABLED)
        self.assertEqual(field_ops_module.status, ModuleRegistrationStatus.ENABLED)
        self.assertEqual(field_ops_module.plugin_api_version, 0)
        self.assertEqual(field_ops_module.platform_min_version, "0.1.0")
        self.assertEqual(field_ops_module.platform_max_version, "0.1.0")
        self.assertEqual(field_ops_module.manifest["runtime_min_version"], "0.1.0")
        self.assertEqual(field_ops_module.manifest["runtime_max_version"], "0.1.0")
        self.assertEqual(field_ops_module.manifest["extensions"]["templates"]["forms"][0]["form_id"], "patient_intake")

        self.assertEqual(ThemeRevision.objects.filter(theme=theme).count(), 1)
        self.assertEqual(theme.current_revision.status, ThemeRevisionStatus.PUBLISHED)
        self.assertEqual(theme.current_revision.payload["theme_id"], "field_ops")

        self.assertEqual(FormRevision.objects.filter(form=form).count(), 1)
        self.assertEqual(form.current_revision.status, FormRevisionStatus.PUBLISHED)
        self.assertEqual(form.current_revision.payload["form_id"], "patient_intake")

        self.assertEqual(AppRevision.objects.filter(app=app).count(), 1)
        self.assertEqual(app.current_revision.status, AppRevisionStatus.PUBLISHED)
        self.assertEqual(app.current_revision.payload["screens"][0]["components"][0]["binding"]["form_id"], "patient_intake")

        self.assertEqual(DeploymentPackage.objects.filter(tenant=tenant).count(), 1)
        self.assertEqual(package.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(package.channel, "dev")
        self.assertEqual(package.app_id, "field_ops_app")
        self.assertEqual(package.payload["tenant_id"], "demo")
        self.assertEqual(package.payload["theme"]["theme_id"], "field_ops")
        self.assertEqual(package.payload["forms"][0]["form_id"], "patient_intake")
        self.assertEqual(package.payload["app"]["app_id"], "field_ops_app")
        self.assertEqual([module["module_id"] for module in package.payload["modules"]], ["core", "field_ops"])
        self.assertTrue(package.package_hash.startswith("sha256:"))
        self.assertTrue(package.signature.startswith("hmac-sha256:"))
        self.assertTrue(verify_deployment_package_hash(package.payload).is_valid)
        self.assertEqual(
            DeploymentPackage.objects.filter(
                tenant=tenant,
                app_id="field_ops_app",
                channel="dev",
                status=DeploymentPackageStatus.ACTIVE,
            ).count(),
            1,
        )
        self.assertEqual(
            AuditEvent.objects.filter(action="deployment-package-activated", target_id=package.package_id).count(),
            1,
        )
        self.assertEqual(AuditEvent.objects.filter(action="demo-seed-plugin-upserted", target_id="field_ops").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="demo-seed-theme-upserted", target_id="field_ops").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="demo-seed-form-upserted", target_id="patient_intake").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="demo-seed-app-upserted", target_id="field_ops_app").count(), 1)
        self.assertEqual(
            AuditEvent.objects.filter(action="demo-seed-package-upserted", target_id=package.package_id).count(),
            1,
        )


class RecordingService(BaseService[str, str]):
    def __init__(self):
        self.steps = []
        self.audit_context = None

    def validate(self, input_data: str, context: ServiceContext) -> None:
        self.steps.append("validate")
        if input_data == "":
            raise ValidationError({"input_data": "Input cannot be blank."})

    def before_execute(self, input_data: str, context: ServiceContext) -> None:
        self.steps.append("before")

    def execute(self, input_data: str, context: ServiceContext) -> str:
        self.steps.append("execute")
        return input_data.upper()

    def after_execute(self, input_data: str, result: ServiceResult[str], context: ServiceContext) -> None:
        self.steps.append("after")

    def audit(self, input_data: str, result: ServiceResult[str], context: ServiceContext) -> None:
        self.steps.append("audit")
        self.audit_context = {
            "actor": context.actor,
            "request_id": context.request_id,
            "result": result.value,
        }


class ServiceLifecycleTests(SimpleTestCase):
    def test_service_lifecycle_runs_in_order(self):
        service = RecordingService()
        context = ServiceContext(actor="user-1", request_id="req-1")

        result = service.run("publish", context)

        self.assertEqual(result.value, "PUBLISH")
        self.assertEqual(service.steps, ["validate", "before", "execute", "after", "audit"])
        self.assertEqual(service.audit_context, {"actor": "user-1", "request_id": "req-1", "result": "PUBLISH"})

    def test_validation_failure_stops_before_execution(self):
        service = RecordingService()

        with self.assertRaises(ValidationError):
            service.run("")

        self.assertEqual(service.steps, ["validate"])

    def test_context_metadata_is_available_and_isolated(self):
        first = ServiceContext(metadata={"source": "test"})
        second = ServiceContext()

        self.assertEqual(first.metadata, {"source": "test"})
        self.assertEqual(second.metadata, {})

    def test_context_metadata_must_be_dictionary(self):
        with self.assertRaises(ValidationError):
            ServiceContext(metadata=["invalid"])


class EventBusTests(SimpleTestCase):
    def test_handlers_receive_matching_events_in_registration_order(self):
        bus = EventBus()
        calls = []

        bus.subscribe("configuration.published", lambda event: calls.append(("first", event.payload["id"])))
        bus.subscribe("configuration.published", lambda event: calls.append(("second", event.payload["id"])))

        results = bus.dispatch(DomainEvent(name="configuration.published", payload={"id": "cfg-1"}))

        self.assertEqual(calls, [("first", "cfg-1"), ("second", "cfg-1")])
        self.assertEqual(results, [None, None])

    def test_dispatch_returns_handler_results(self):
        bus = EventBus()

        bus.subscribe("module.registered", lambda event: event.payload["module_id"])
        bus.subscribe("module.registered", lambda event: event.metadata["source"])

        results = bus.dispatch(
            DomainEvent(
                name="module.registered",
                payload={"module_id": "core"},
                metadata={"source": "test"},
            )
        )

        self.assertEqual(results, ["core", "test"])

    def test_dispatch_without_handlers_returns_empty_list(self):
        bus = EventBus()

        results = bus.dispatch(DomainEvent(name="unused.event"))

        self.assertEqual(results, [])

    def test_unsubscribe_removes_handler(self):
        bus = EventBus()
        calls = []

        def handler(event):
            calls.append(event.name)

        unsubscribe = bus.subscribe("identity.role-assigned", handler)
        unsubscribe()

        bus.dispatch(DomainEvent(name="identity.role-assigned"))

        self.assertEqual(calls, [])

    def test_reset_removes_all_handlers(self):
        bus = EventBus()
        calls = []

        bus.subscribe("security.login-failed", lambda event: calls.append(event.name))
        bus.reset()

        bus.dispatch(DomainEvent(name="security.login-failed"))

        self.assertEqual(calls, [])

    def test_event_payload_and_metadata_must_be_dictionaries(self):
        with self.assertRaises(ValidationError):
            DomainEvent(name="bad.payload", payload=["invalid"])

        with self.assertRaises(ValidationError):
            DomainEvent(name="bad.metadata", metadata=["invalid"])

    def test_event_name_and_handler_are_required(self):
        bus = EventBus()

        with self.assertRaises(ValidationError):
            DomainEvent(name="")

        with self.assertRaises(ValidationError):
            bus.subscribe("", lambda event: None)

        with self.assertRaises(ValidationError):
            bus.subscribe("valid.event", None)


class ApiErrorModelTests(SimpleTestCase):
    def test_api_error_serializes_stable_shape(self):
        error = ApiError(
            code=ApiErrorCode.VALIDATION_ERROR,
            message="Validation failed.",
            status_code=400,
            details=[
                ApiErrorDetail(field="name", message="Name is required."),
            ],
            request_id="req-1",
            correlation_id="corr-1",
        )

        self.assertEqual(
            error.to_dict(),
            {
                "error": {
                    "code": "validation_error",
                    "message": "Validation failed.",
                    "status_code": 400,
                    "details": [
                        {
                            "code": "validation_error",
                            "message": "Name is required.",
                            "field": "name",
                        }
                    ],
                    "request_id": "req-1",
                    "correlation_id": "corr-1",
                }
            },
        )

    def test_error_detail_without_field_omits_field_key(self):
        detail = ApiErrorDetail(code="custom", message="General problem.")

        self.assertEqual(detail.to_dict(), {"code": "custom", "message": "General problem."})

    def test_api_error_response_uses_error_status_and_body(self):
        error = ApiError(code=ApiErrorCode.NOT_FOUND, message="Object not found.", status_code=404)

        response = api_error_response(error)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.content.decode(),
            '{"error": {"code": "not_found", "message": "Object not found.", "status_code": 404, "details": []}}',
        )

    def test_api_error_rejects_invalid_status_code(self):
        with self.assertRaises(ValidationError):
            ApiError(code=ApiErrorCode.INTERNAL_ERROR, message="Nope.", status_code=200)

    def test_api_error_requires_code_and_message(self):
        with self.assertRaises(ValidationError):
            ApiError(code="", message="Missing code.")

        with self.assertRaises(ValidationError):
            ApiError(code=ApiErrorCode.CONFLICT, message="")

    def test_api_error_details_must_be_detail_objects(self):
        with self.assertRaises(ValidationError):
            ApiError(code=ApiErrorCode.VALIDATION_ERROR, message="Invalid.", details=[{"field": "name"}])

    def test_api_error_detail_requires_code_and_message(self):
        with self.assertRaises(ValidationError):
            ApiErrorDetail(code="", message="Missing code.")

        with self.assertRaises(ValidationError):
            ApiErrorDetail(code=ApiErrorCode.VALIDATION_ERROR, message="")


class BackgroundJobRegistryTests(SimpleTestCase):
    def test_registry_runs_registered_handler(self):
        registry = BackgroundJobRegistry()
        registry.register("package.compile", lambda job: {"package_id": job.payload["package_id"]})

        result = registry.run(BackgroundJob(name="package.compile", payload={"package_id": "pkg-1"}))

        self.assertEqual(result.status, BackgroundJobStatus.SUCCEEDED)
        self.assertEqual(result.value, {"package_id": "pkg-1"})

    def test_registry_returns_failed_result_when_handler_raises(self):
        registry = BackgroundJobRegistry()

        def handler(_job):
            raise RuntimeError("compile failed")

        registry.register("package.compile", handler)

        result = registry.run(BackgroundJob(name="package.compile"))

        self.assertEqual(result.status, BackgroundJobStatus.FAILED)
        self.assertEqual(result.error, "compile failed")

    def test_registry_rejects_missing_handler(self):
        registry = BackgroundJobRegistry()

        with self.assertRaises(ValidationError):
            registry.run(BackgroundJob(name="missing.job"))

    def test_unregister_and_reset_remove_handlers(self):
        registry = BackgroundJobRegistry()
        registry.register("first.job", lambda job: "first")
        registry.register("second.job", lambda job: "second")

        registry.unregister("first.job")
        registry.reset()

        with self.assertRaises(ValidationError):
            registry.run(BackgroundJob(name="second.job"))

    def test_job_validates_required_shape(self):
        with self.assertRaises(ValidationError):
            BackgroundJob(name="")

        with self.assertRaises(ValidationError):
            BackgroundJob(name="bad.payload", payload=["invalid"])

        with self.assertRaises(ValidationError):
            BackgroundJob(name="bad.metadata", metadata=["invalid"])

    def test_registry_rejects_invalid_registration(self):
        registry = BackgroundJobRegistry()

        with self.assertRaises(ValidationError):
            registry.register("", lambda job: None)

        with self.assertRaises(ValidationError):
            registry.register("valid.job", None)

    def test_job_result_validates_status_and_metadata(self):
        job = BackgroundJob(name="test.job")

        with self.assertRaises(ValidationError):
            BackgroundJobResult(job=job, status="unknown")

        with self.assertRaises(ValidationError):
            BackgroundJobResult(job=job, status=BackgroundJobStatus.SUCCEEDED, metadata=["invalid"])
