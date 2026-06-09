from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.urls import reverse

from apps.core.services import BaseService, ServiceContext, ServiceResult


class HealthEndpointTests(SimpleTestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


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
