from __future__ import annotations

import subprocess
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = ROOT / "frontend-admin"
PACKAGE_LOCK = FRONTEND_ROOT / "package-lock.json"
NPM = shutil.which("npm") or shutil.which("npm.cmd")


def run(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=FRONTEND_ROOT, check=True)


def main() -> int:
    if not PACKAGE_LOCK.exists():
        raise FileNotFoundError(f"Frontend package lock not found: {PACKAGE_LOCK}")
    if not NPM:
        raise FileNotFoundError("npm executable not found on PATH")

    run([NPM, "ci"])
    run([NPM, "run", "validate"])
    print("Frontend admin validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
