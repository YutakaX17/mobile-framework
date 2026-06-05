import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v1" / "theme.schema.json"
VALID_FIXTURE = ROOT / "fixtures" / "valid" / "v1" / "theme-basic.json"
INVALID_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "theme-missing-name.json",
    ROOT / "fixtures" / "invalid" / "v1" / "theme-invalid-color.json",
    ROOT / "fixtures" / "invalid" / "v1" / "theme-unknown-mode.json",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class ThemeSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_valid_basic_theme_fixture(self) -> None:
        theme = load_json(VALID_FIXTURE)
        self.validator.validate(theme)

    def test_invalid_theme_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FIXTURES:
            with self.subTest(fixture=fixture.name):
                theme = load_json(fixture)
                with self.assertRaises(ValidationError):
                    self.validator.validate(theme)


if __name__ == "__main__":
    unittest.main()
