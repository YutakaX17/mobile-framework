from __future__ import annotations

import argparse
import json
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource


CONTRACTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = CONTRACTS_ROOT.parent
DEFAULT_MANIFEST = CONTRACTS_ROOT / "validation_manifest.json"
FIXTURE_ROOTS = (
    CONTRACTS_ROOT / "fixtures" / "valid",
    CONTRACTS_ROOT / "fixtures" / "invalid",
)


@dataclass(frozen=True)
class ValidationResult:
    checked_schemas: int
    checked_valid_fixtures: int
    checked_invalid_fixtures: int


class ContractValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def contract_path(relative_path: str) -> Path:
    path = (CONTRACTS_ROOT / relative_path).resolve()
    if not path.is_relative_to(CONTRACTS_ROOT):
        raise ContractValidationError(f"Path escapes contracts root: {relative_path}")
    return path


def load_manifest(path: Path) -> dict:
    manifest = load_json(path)
    if manifest.get("schema_version") != "v1":
        raise ContractValidationError("validation_manifest.json must declare schema_version v1")
    if not isinstance(manifest.get("schemas"), dict) or not manifest["schemas"]:
        raise ContractValidationError("validation_manifest.json must contain schemas")
    return manifest


def load_schemas(manifest: dict) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for name, config in manifest["schemas"].items():
        schema_path = contract_path(config["schema"])
        if not schema_path.exists():
            raise ContractValidationError(f"Schema not found for {name}: {schema_path}")
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
        schema_id = schema.get("$id")
        if not schema_id:
            raise ContractValidationError(f"Schema {schema_path} is missing $id")
        if schema_id in seen_ids:
            raise ContractValidationError(f"Duplicate schema $id: {schema_id}")
        seen_ids.add(schema_id)
        schemas[name] = schema
    return schemas


def build_registry(schemas: dict[str, dict]) -> Registry:
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


def validate_fixture_coverage(manifest: dict) -> None:
    listed = set()
    for config in manifest["schemas"].values():
        for key in ("valid", "invalid"):
            fixtures = config.get(key, [])
            if not fixtures:
                raise ContractValidationError(f"Schema {config['schema']} has no {key} fixtures")
            for fixture in fixtures:
                listed.add(contract_path(fixture))

    discovered = set()
    for root in FIXTURE_ROOTS:
        discovered.update(path.resolve() for path in root.rglob("*.json"))

    missing_from_manifest = sorted(discovered - listed)
    missing_from_disk = sorted(path for path in listed if not path.exists())

    if missing_from_manifest:
        paths = "\n".join(str(path.relative_to(CONTRACTS_ROOT)) for path in missing_from_manifest)
        raise ContractValidationError(f"Fixtures missing from validation manifest:\n{paths}")
    if missing_from_disk:
        paths = "\n".join(str(path.relative_to(CONTRACTS_ROOT)) for path in missing_from_disk)
        raise ContractValidationError(f"Manifest references missing fixtures:\n{paths}")


def validate_contracts(manifest_path: Path = DEFAULT_MANIFEST) -> ValidationResult:
    manifest = load_manifest(manifest_path)
    schemas = load_schemas(manifest)
    registry = build_registry(schemas)
    validate_fixture_coverage(manifest)

    valid_count = 0
    invalid_count = 0

    for name, config in manifest["schemas"].items():
        validator = Draft202012Validator(schemas[name], registry=registry)
        for fixture in config["valid"]:
            fixture_path = contract_path(fixture)
            validator.validate(load_json(fixture_path))
            valid_count += 1
        for fixture in config["invalid"]:
            fixture_path = contract_path(fixture)
            try:
                validator.validate(load_json(fixture_path))
            except ValidationError:
                invalid_count += 1
            else:
                raise ContractValidationError(f"Invalid fixture unexpectedly passed: {fixture}")

    return ValidationResult(
        checked_schemas=len(schemas),
        checked_valid_fixtures=valid_count,
        checked_invalid_fixtures=invalid_count,
    )


def run_unittest_suite() -> unittest.result.TestResult:
    repo_root = str(REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    suite = unittest.defaultTestLoader.discover(str(CONTRACTS_ROOT / "tests"))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate contract schemas and fixtures.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to the contract validation manifest.",
    )
    parser.add_argument(
        "--skip-unittest",
        action="store_true",
        help="Only run manifest-driven schema and fixture validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = validate_contracts(args.manifest)
        print(
            "Validated "
            f"{result.checked_schemas} schemas, "
            f"{result.checked_valid_fixtures} valid fixtures, and "
            f"{result.checked_invalid_fixtures} invalid fixtures."
        )
        if not args.skip_unittest:
            unittest_result = run_unittest_suite()
            if not unittest_result.wasSuccessful():
                return 1
    except Exception as exc:  # noqa: BLE001 - CLI should report any validation failure cleanly.
        print(f"Contract validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

