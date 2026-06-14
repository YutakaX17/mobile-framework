import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "v1" / "component.schema.json"
VALID_FIXTURE = ROOT / "fixtures" / "valid" / "v1" / "component-card-with-action.json"
INVALID_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "component-missing-component-id.json",
    ROOT / "fixtures" / "invalid" / "v1" / "component-unknown-type.json",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class ComponentSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA)
        Draft202012Validator.check_schema(cls.schema)
        registry = Registry().with_resource(cls.schema["$id"], Resource.from_contents(cls.schema))
        cls.validator = Draft202012Validator(cls.schema, registry=registry)

    def test_valid_component_fixture(self) -> None:
        self.validator.validate(load_json(VALID_FIXTURE))

    def test_invalid_component_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FIXTURES:
            with self.subTest(fixture=fixture.name):
                with self.assertRaises(ValidationError):
                    self.validator.validate(load_json(fixture))


if __name__ == "__main__":
    unittest.main()
