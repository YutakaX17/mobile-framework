from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_ROOT = ROOT / "contracts"
SCHEMA_ROOT = CONTRACTS_ROOT / "schemas" / "v1"

CONFIGURATION_SCHEMA_FILES = {
    "action": "action.schema.json",
    "app": "app.schema.json",
    "component": "component.schema.json",
    "deployment_package": "deployment-package.schema.json",
    "field": "field.schema.json",
    "form": "form.schema.json",
    "screen": "screen.schema.json",
    "theme": "theme.schema.json",
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def configuration_schemas() -> dict[str, dict[str, Any]]:
    schemas = {}
    for kind, filename in CONFIGURATION_SCHEMA_FILES.items():
        schema = _load_json(SCHEMA_ROOT / filename)
        Draft202012Validator.check_schema(schema)
        schemas[kind] = schema
    return schemas


@lru_cache(maxsize=1)
def configuration_schema_registry() -> Registry:
    registry = Registry()
    for schema in configuration_schemas().values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


def configuration_validator(kind: str) -> Draft202012Validator:
    schemas = configuration_schemas()
    if kind not in schemas:
        raise ValidationError({"kind": f"Unsupported configuration kind `{kind}`."})
    return Draft202012Validator(schemas[kind], registry=configuration_schema_registry())


def validate_configuration_payload(kind: str, payload: dict[str, Any]) -> None:
    try:
        configuration_validator(kind).validate(payload)
    except JsonSchemaValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = f" at {path}" if path else ""
        raise ValidationError({"payload": f"Invalid {kind} configuration{location}: {exc.message}"}) from exc
