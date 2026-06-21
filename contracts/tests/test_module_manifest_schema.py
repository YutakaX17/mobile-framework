import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v1" / "module-manifest.schema.json"
VALID_FIXTURES = [
    ROOT / "fixtures" / "valid" / "v1" / "module-manifest-core.json",
    ROOT / "fixtures" / "valid" / "v1" / "module-manifest-field-ops.json",
]
INVALID_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "module-manifest-missing-module-id.json",
    ROOT / "fixtures" / "invalid" / "v1" / "module-manifest-invalid-version.json",
    ROOT / "fixtures" / "invalid" / "v1" / "module-manifest-unknown-surface.json",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class ModuleManifestSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_valid_manifest_fixtures(self) -> None:
        for fixture in VALID_FIXTURES:
            with self.subTest(fixture=fixture.name):
                manifest = load_json(fixture)
                self.validator.validate(manifest)

    def test_invalid_manifest_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FIXTURES:
            with self.subTest(fixture=fixture.name):
                manifest = load_json(fixture)
                with self.assertRaises(ValidationError):
                    self.validator.validate(manifest)


if __name__ == "__main__":
    unittest.main()
