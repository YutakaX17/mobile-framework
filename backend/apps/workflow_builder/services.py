from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_SCHEMA = ROOT / "contracts" / "schemas" / "v1" / "workflow.schema.json"


@lru_cache(maxsize=1)
def workflow_schema() -> dict[str, Any]:
    with WORKFLOW_SCHEMA.open(encoding="utf-8-sig") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=1)
def workflow_validator() -> Draft202012Validator:
    return Draft202012Validator(workflow_schema())


def validate_workflow_payload(payload: dict[str, Any]) -> None:
    try:
        workflow_validator().validate(payload)
    except JsonSchemaValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = f" at {path}" if path else ""
        raise ValidationError({"payload": f"Invalid workflow definition{location}: {exc.message}"}) from exc
