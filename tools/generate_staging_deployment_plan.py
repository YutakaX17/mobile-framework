from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "deploy" / "staging-plan.json"

STAGING_SERVICES = [
    {
        "name": "backend",
        "image": "mobile-framework-backend",
        "dockerfile": "backend/Dockerfile",
        "context": "backend",
        "healthcheck": "/health/",
        "requires": ["postgres", "redis"],
    },
    {
        "name": "frontend-admin",
        "image": "mobile-framework-frontend-admin",
        "dockerfile": "frontend-admin/Dockerfile",
        "context": "frontend-admin",
        "healthcheck": "/",
        "requires": ["backend"],
    },
]


def validate_required_files() -> None:
    required_files = [
        ROOT / "backend" / "Dockerfile",
        ROOT / "frontend-admin" / "Dockerfile",
        ROOT / ".github" / "workflows" / "docker-build.yml",
        ROOT / ".github" / "workflows" / "image-signing.yml",
        ROOT / ".github" / "workflows" / "sbom-generation.yml",
    ]
    missing = [path.relative_to(ROOT).as_posix() for path in required_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing staging deployment prerequisites: {', '.join(missing)}")


def build_plan() -> dict[str, Any]:
    validate_required_files()
    return {
        "schema_version": "staging-deployment-plan.v1",
        "environment": "staging",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": "dry-run",
        "repository": "YutakaX17/mobile-framework",
        "pre_deploy_checks": [
            "Docker Build",
            "Image Signing",
            "SBOM Generation",
            "Secret Scan",
            "CodeQL",
        ],
        "services": STAGING_SERVICES,
        "promotion_gates": [
            "All required checks pass on main",
            "Signed image digest bundles are retained as workflow artifacts",
            "SBOM artifact is retained as a workflow artifact",
            "Staging environment secrets are configured before real deployment is enabled",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a dry-run staging deployment plan.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated staging deployment plan for {len(plan['services'])} services: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
