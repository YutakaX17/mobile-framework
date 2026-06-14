import tempfile
import unittest
import py_compile
from pathlib import Path

from contracts.generate_types import (
    check_all,
    check_kotlin,
    check_python,
    check_typescript,
    generate_kotlin,
    generate_python,
    generate_typescript,
    write_all,
    write_kotlin,
    write_python,
    write_typescript,
)


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

    def test_python_generation_is_deterministic(self) -> None:
        first = generate_python()
        second = generate_python()

        self.assertEqual(first, second)
        self.assertIn("class ModuleManifest(TypedDict):", first)
        self.assertIn("class DeploymentPackage(TypedDict):", first)
        self.assertIn("JsonValue: TypeAlias", first)

    def test_python_check_accepts_current_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "contracts.py"
            write_python(output_path)

            check_python(output_path)
            py_compile.compile(str(output_path), doraise=True)

    def test_kotlin_generation_is_deterministic(self) -> None:
        first = generate_kotlin()
        second = generate_kotlin()

        self.assertEqual(first, second)
        self.assertIn("public data class ModuleManifest(", first)
        self.assertIn("public data class DeploymentPackage(", first)
        self.assertIn("public typealias JsonValue", first)
        self.assertNotIn(" | ", first)

    def test_kotlin_check_accepts_current_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "Contracts.kt"
            write_kotlin(output_path)

            check_kotlin(output_path)

    def test_all_check_accepts_current_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            typescript_output = Path(directory) / "contracts.d.ts"
            python_output = Path(directory) / "contracts.py"
            kotlin_output = Path(directory) / "Contracts.kt"
            write_all(typescript_output=typescript_output, python_output=python_output, kotlin_output=kotlin_output)

            check_all(typescript_output=typescript_output, python_output=python_output, kotlin_output=kotlin_output)


if __name__ == "__main__":
    unittest.main()
