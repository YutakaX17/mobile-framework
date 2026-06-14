from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


ROOT = Path(__file__).resolve().parents[3]
MODULE_MANIFEST_SCHEMA = ROOT / "contracts" / "schemas" / "v1" / "module-manifest.schema.json"
CURRENT_PLATFORM_VERSION = "0.1.0"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
CONSTRAINT_RE = re.compile(r"^(<=|>=|<|>|=)?\s*(.+)$")
ACTIVE_DEPENDENCY_STATUSES = {"registered", "enabled"}


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


def parse_semver(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(version)
    if not match:
        raise ValidationError(f"Invalid semantic version: {version}")
    return tuple(int(part) for part in match.groups())


def version_satisfies(version: str, constraint: str) -> bool:
    constraint = constraint.strip()
    if constraint == "*":
        return True

    version_value = parse_semver(version)
    for clause in [part.strip() for part in constraint.split(",") if part.strip()]:
        match = CONSTRAINT_RE.match(clause)
        if not match:
            raise ValidationError(f"Invalid dependency version constraint: {constraint}")
        operator = match.group(1) or "="
        expected_value = parse_semver(match.group(2))
        if operator == "=" and version_value != expected_value:
            return False
        if operator == ">" and version_value <= expected_value:
            return False
        if operator == ">=" and version_value < expected_value:
            return False
        if operator == "<" and version_value >= expected_value:
            return False
        if operator == "<=" and version_value > expected_value:
            return False
    return True


def validate_module_compatibility(registration, platform_version: str = CURRENT_PLATFORM_VERSION) -> None:
    platform_value = parse_semver(platform_version)
    minimum_value = parse_semver(registration.platform_min_version)
    maximum_value = parse_semver(registration.platform_max_version) if registration.platform_max_version else None
    errors = []

    if maximum_value and minimum_value > maximum_value:
        errors.append("Platform minimum version cannot be greater than platform maximum version.")
    if minimum_value > platform_value:
        errors.append(
            f"Module `{registration.module_id}` requires platform version "
            f"{registration.platform_min_version} or newer; current platform version is {platform_version}."
        )
    if maximum_value and maximum_value < platform_value:
        errors.append(
            f"Module `{registration.module_id}` supports platform versions up to "
            f"{registration.platform_max_version}; current platform version is {platform_version}."
        )

    if errors:
        raise ValidationError({"platform_min_version": errors})


def validate_module_dependencies(registration, registrations) -> None:
    dependencies = registration.manifest.get("dependencies", [])
    seen_module_ids = set()
    errors = []

    for dependency in dependencies:
        module_id = dependency["module_id"]
        constraint = dependency["version_constraint"]
        optional = dependency.get("optional", False)

        if module_id == registration.module_id:
            errors.append(f"Module `{registration.module_id}` cannot depend on itself.")
            continue
        if module_id in seen_module_ids:
            errors.append(f"Module dependency `{module_id}` is declared more than once.")
            continue
        seen_module_ids.add(module_id)

        candidates = registrations.filter(
            module_id=module_id,
            status__in=ACTIVE_DEPENDENCY_STATUSES,
        )
        if registration.pk:
            candidates = candidates.exclude(pk=registration.pk)

        installed = list(candidates)
        if not installed:
            if not optional:
                errors.append(f"Required module dependency `{module_id}` is not registered.")
            continue

        try:
            if not any(version_satisfies(candidate.version, constraint) for candidate in installed):
                versions = ", ".join(candidate.version for candidate in installed)
                errors.append(
                    f"Module dependency `{module_id}` does not satisfy `{constraint}` "
                    f"(registered versions: {versions})."
                )
        except ValidationError as exc:
            errors.extend(exc.messages)

    if errors:
        raise ValidationError({"dependencies": errors})
