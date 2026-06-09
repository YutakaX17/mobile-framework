from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.urls import reverse

from apps.core.events import DomainEvent, EventBus
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
