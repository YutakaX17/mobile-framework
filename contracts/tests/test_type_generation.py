import tempfile
import unittest
from pathlib import Path

from contracts.generate_types import check_typescript, generate_typescript, write_typescript


class TypeGenerationTest(unittest.TestCase):
    def test_typescript_generation_is_deterministic(self) -> None:
        first = generate_typescript()
        second = generate_typescript()

        self.assertEqual(first, second)
        self.assertIn("export interface ModuleManifest", first)
        self.assertIn("export interface DeploymentPackage", first)
        self.assertIn("export type JsonValue", first)

    def test_typescript_check_accepts_current_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "contracts.d.ts"
            write_typescript(output_path)

            check_typescript(output_path)


if __name__ == "__main__":
    unittest.main()
