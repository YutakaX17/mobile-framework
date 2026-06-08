from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=BACKEND, check=True)


def main() -> int:
    commands = [
        [sys.executable, "manage.py", "check"],
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        [
            sys.executable,
            "manage.py",
            "test",
            "apps.core",
            "apps.tenants",
            "apps.identity",
            "--settings=config.settings.test",
        ],
    ]
    try:
        for command in commands:
            run(command)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    print("Backend validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
