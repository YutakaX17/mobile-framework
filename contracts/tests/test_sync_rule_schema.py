import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "v1" / "sync-rule.schema.json"
VALID_FIXTURE = ROOT / "fixtures" / "valid" / "v1" / "sync-rule-patient-submissions.json"
INVALID_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "sync-rule-missing-entity-type.json",
    ROOT / "fixtures" / "invalid" / "v1" / "sync-rule-unknown-conflict-policy.json",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class SyncRuleSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_valid_sync_rule_fixture(self) -> None:
        self.validator.validate(load_json(VALID_FIXTURE))

    def test_invalid_sync_rule_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FIXTURES:
            with self.subTest(fixture=fixture.name):
                with self.assertRaises(ValidationError):
                    self.validator.validate(load_json(fixture))


if __name__ == "__main__":
    unittest.main()
