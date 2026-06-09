from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

from django.core.exceptions import ValidationError


EventHandler = Callable[["DomainEvent"], Any]


@dataclass(frozen=True)
class DomainEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    tenant: Any | None = None
    actor: Any | None = None
    request_id: str = ""
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        errors = {}
        if not self.name:
            errors["name"] = "Domain event name is required."
        if not isinstance(self.payload, dict):
            errors["payload"] = "Domain event payload must be a dictionary."
        if not isinstance(self.metadata, dict):
            errors["metadata"] = "Domain event metadata must be a dictionary."
        if errors:
            raise ValidationError(errors)


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> Callable[[], None]:
        if not event_name:
            raise ValidationError({"event_name": "Event name is required."})
        if not callable(handler):
            raise ValidationError({"handler": "Event handler must be callable."})

        self._handlers[event_name].append(handler)

        def unsubscribe() -> None:
            self.unsubscribe(event_name, handler)

        return unsubscribe

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_name, [])
        self._handlers[event_name] = [registered for registered in handlers if registered is not handler]
        if not self._handlers[event_name]:
            self._handlers.pop(event_name, None)

    def dispatch(self, event: DomainEvent) -> list[Any]:
        handlers = list(self._handlers.get(event.name, []))
        return [handler(event) for handler in handlers]

    def reset(self) -> None:
        self._handlers.clear()


default_event_bus = EventBus()
