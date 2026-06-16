import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v1" / "mobile-form-submission.schema.json"
VALID_FIXTURE = ROOT / "fixtures" / "valid" / "v1" / "mobile-form-submission-patient-intake.json"
INVALID_FIXTURES = [
    ROOT / "fixtures" / "invalid" / "v1" / "mobile-form-submission-invalid-answers.json",
    ROOT / "fixtures" / "invalid" / "v1" / "mobile-form-submission-missing-local-id.json",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class MobileFormSubmissionSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def test_valid_mobile_form_submission_fixture(self) -> None:
        payload = load_json(VALID_FIXTURE)
        self.validator.validate(payload)

    def test_invalid_mobile_form_submission_fixtures_fail_validation(self) -> None:
        for fixture in INVALID_FIXTURES:
            with self.subTest(fixture=fixture.name):
                payload = load_json(fixture)
                with self.assertRaises(ValidationError):
                    self.validator.validate(payload)


if __name__ == "__main__":
    unittest.main()
