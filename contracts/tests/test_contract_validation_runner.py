import unittest

from contracts.validate_contracts import DEFAULT_MANIFEST, load_manifest, validate_contracts


class ContractValidationRunnerTest(unittest.TestCase):
    def test_manifest_driven_validation_passes(self) -> None:
        manifest = load_manifest(DEFAULT_MANIFEST)
        result = validate_contracts()
        self.assertEqual(result.checked_schemas, len(manifest["schemas"]))
        self.assertEqual(
            result.checked_valid_fixtures,
            sum(len(config["valid"]) for config in manifest["schemas"].values()),
        )
        self.assertEqual(
            result.checked_invalid_fixtures,
            sum(len(config["invalid"]) for config in manifest["schemas"].values()),
        )


if __name__ == "__main__":
    unittest.main()
