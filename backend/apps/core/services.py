from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from django.core.exceptions import ValidationError


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass
class ServiceContext:
    tenant: Any | None = None
    actor: Any | None = None
    request_id: str = ""
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, dict):
            raise ValidationError({"metadata": "Service context metadata must be a dictionary."})


@dataclass(frozen=True)
class ServiceResult(Generic[OutputT]):
    value: OutputT
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseService(Generic[InputT, OutputT]):
    def run(self, input_data: InputT, context: ServiceContext | None = None) -> ServiceResult[OutputT]:
        context = context or ServiceContext()

        self.validate(input_data, context)
        self.before_execute(input_data, context)
        value = self.execute(input_data, context)
        result = ServiceResult(value=value)
        self.after_execute(input_data, result, context)
        self.audit(input_data, result, context)
        return result

    def validate(self, input_data: InputT, context: ServiceContext) -> None:
        return None

    def before_execute(self, input_data: InputT, context: ServiceContext) -> None:
        return None

    def execute(self, input_data: InputT, context: ServiceContext) -> OutputT:
        raise NotImplementedError

    def after_execute(self, input_data: InputT, result: ServiceResult[OutputT], context: ServiceContext) -> None:
        return None

    def audit(self, input_data: InputT, result: ServiceResult[OutputT], context: ServiceContext) -> None:
        return None
