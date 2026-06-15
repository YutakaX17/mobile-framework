from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "backend" / "rust_ext"
MANIFEST = ROOT / "backend" / "rust_ext" / "Cargo.toml"
WRAPPER_TESTS = ROOT / "backend" / "rust_ext" / "tests"


def run(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Rust extension manifest not found: {MANIFEST}")

    include_python_wrapper = "--include-python-wrapper" in sys.argv[1:]
    run(["cargo", "fmt", "--manifest-path", str(MANIFEST), "--check"])
    run(["cargo", "test", "--manifest-path", str(MANIFEST)])
    if include_python_wrapper:
        run([sys.executable, "-m", "pip", "install", str(PACKAGE_ROOT)])
        run([sys.executable, "-m", "unittest", "discover", "-s", str(WRAPPER_TESTS)])
    print("Rust extension validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
