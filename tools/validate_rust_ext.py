from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "backend" / "rust_ext" / "Cargo.toml"


def run(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Rust extension manifest not found: {MANIFEST}")

    run(["cargo", "fmt", "--manifest-path", str(MANIFEST), "--check"])
    run(["cargo", "test", "--manifest-path", str(MANIFEST)])
    print("Rust extension validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
