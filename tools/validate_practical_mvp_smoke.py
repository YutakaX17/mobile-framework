from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SMOKE_TEST = (
    "tests.test_integration."
    "PracticalMvpBuilderIntegrationTests."
    "test_practical_mvp_smoke_path_from_admin_publish_to_mobile_sync"
)


def main() -> int:
    command = [
        sys.executable,
        "manage.py",
        "test",
        SMOKE_TEST,
        "--settings=config.settings.test",
    ]
    try:
        subprocess.run(command, cwd=BACKEND, check=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    print("Practical MVP smoke validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
