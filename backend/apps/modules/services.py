from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


ROOT = Path(__file__).resolve().parents[3]
MODULE_MANIFEST_SCHEMA = ROOT / "contracts" / "schemas" / "v1" / "module-manifest.schema.json"


@lru_cache(maxsize=1)
def module_manifest_validator() -> Draft202012Validator:
    with MODULE_MANIFEST_SCHEMA.open(encoding="utf-8-sig") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_module_manifest(manifest: dict[str, Any]) -> None:
    try:
        module_manifest_validator().validate(manifest)
    except JsonSchemaValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = f" at {path}" if path else ""
        raise ValidationError(f"Invalid module manifest{location}: {exc.message}") from exc
