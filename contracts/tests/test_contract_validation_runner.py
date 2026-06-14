import unittest

from contracts.validate_contracts import validate_contracts


class ContractValidationRunnerTest(unittest.TestCase):
    def test_manifest_driven_validation_passes(self) -> None:
        result = validate_contracts()
        self.assertEqual(result.checked_schemas, 9)
        self.assertEqual(result.checked_valid_fixtures, 9)
        self.assertEqual(result.checked_invalid_fixtures, 16)


if __name__ == "__main__":
    unittest.main()
