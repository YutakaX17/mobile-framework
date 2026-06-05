import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
FIELD_SCHEMA_PATH = ROOT / "schemas" / "v1" / "field.schema.json"
FORM_SCHEMA_PATH = ROOT / "schemas" / "v1" / "form.schema.json"
VALID_FORM_FIXTURE = ROOT / "fixtures" / "valid" / "v1" / "form-patient-intake.json"
VALID_FIELD_FIXTURE = ROOT / "fixtures" / "valid" / "v1" / "field-select-gender.json"
INVALID_FIELD_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "field-select-missing-options.json",
    ROOT / "fixtures" / "invalid" / "v1" / "field-unknown-type.json",
]
INVALID_FORM_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "form-missing-fields.json",
    ROOT / "fixtures" / "invalid" / "v1" / "form-unknown-mode.json",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class FormFieldSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.field_schema = load_json(FIELD_SCHEMA_PATH)
        cls.form_schema = load_json(FORM_SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.field_schema)
        Draft202012Validator.check_schema(cls.form_schema)
        registry = Registry().with_resource(
            cls.field_schema["$id"],
            Resource.from_contents(cls.field_schema),
        )
        cls.field_validator = Draft202012Validator(cls.field_schema)
        cls.form_validator = Draft202012Validator(cls.form_schema, registry=registry)

    def test_valid_field_fixture(self) -> None:
        field = load_json(VALID_FIELD_FIXTURE)
        self.field_validator.validate(field)

    def test_invalid_field_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FIELD_FIXTURES:
            with self.subTest(fixture=fixture.name):
                field = load_json(fixture)
                with self.assertRaises(ValidationError):
                    self.field_validator.validate(field)

    def test_valid_form_fixture(self) -> None:
        form = load_json(VALID_FORM_FIXTURE)
        self.form_validator.validate(form)

    def test_invalid_form_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FORM_FIXTURES:
            with self.subTest(fixture=fixture.name):
                form = load_json(fixture)
                with self.assertRaises(ValidationError):
                    self.form_validator.validate(form)


if __name__ == "__main__":
    unittest.main()
