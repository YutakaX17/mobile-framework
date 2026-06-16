import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v1"
FIXTURES = ROOT / "fixtures"

SCHEMA_NAMES = [
    "module-manifest.schema.json",
    "theme.schema.json",
    "field.schema.json",
    "form.schema.json",
    "action.schema.json",
    "component.schema.json",
    "screen.schema.json",
    "app.schema.json",
    "deployment-package.schema.json",
]

VALID_FIXTURES = {
    "action.schema.json": FIXTURES / "valid" / "v1" / "action-navigate-home.json",
    "component.schema.json": FIXTURES / "valid" / "v1" / "component-card-with-action.json",
    "screen.schema.json": FIXTURES / "valid" / "v1" / "screen-intake.json",
    "app.schema.json": FIXTURES / "valid" / "v1" / "app-field-ops.json",
    "deployment-package.schema.json": FIXTURES / "valid" / "v1" / "deployment-package-field-ops.json",
}

INVALID_FIXTURES = {
    "action.schema.json": [FIXTURES / "invalid" / "v1" / "action-unknown-type.json"],
    "component.schema.json": [
        FIXTURES / "invalid" / "v1" / "component-missing-component-id.json",
        FIXTURES / "invalid" / "v1" / "component-unknown-type.json",
    ],
    "screen.schema.json": [FIXTURES / "invalid" / "v1" / "screen-form-missing-form-component.json"],
    "app.schema.json": [
        FIXTURES / "invalid" / "v1" / "app-missing-navigation.json",
        FIXTURES / "invalid" / "v1" / "app-navigation-invalid-order.json",
    ],
    "deployment-package.schema.json": [FIXTURES / "invalid" / "v1" / "deployment-package-invalid-hash.json"],
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def build_registry(schemas: dict[str, dict]) -> Registry:
    registry = Registry()
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


class AppPackageSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: load_json(SCHEMA_DIR / name) for name in SCHEMA_NAMES}
        for schema in cls.schemas.values():
            Draft202012Validator.check_schema(schema)
        cls.registry = build_registry(cls.schemas)

    def validator_for(self, schema_name: str) -> Draft202012Validator:
        return Draft202012Validator(self.schemas[schema_name], registry=self.registry)

    def test_valid_app_package_fixtures(self) -> None:
        for schema_name, fixture in VALID_FIXTURES.items():
            with self.subTest(schema=schema_name, fixture=fixture.name):
                self.validator_for(schema_name).validate(load_json(fixture))

    def test_invalid_app_package_fixtures_fail_validation(self) -> None:
        for schema_name, fixtures in INVALID_FIXTURES.items():
            validator = self.validator_for(schema_name)
            for fixture in fixtures:
                with self.subTest(schema=schema_name, fixture=fixture.name):
                    with self.assertRaises(ValidationError):
                        validator.validate(load_json(fixture))


if __name__ == "__main__":
    unittest.main()
