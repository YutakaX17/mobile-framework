from __future__ import annotations

from typing import Any

from apps.configurations.services import validate_configuration_payload


def validate_deployment_package_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("deployment_package", payload)
