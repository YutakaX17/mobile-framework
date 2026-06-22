from __future__ import annotations

import argparse
import json
import re
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "release" / "release-manifest.json"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
PLATFORM_VERSION_RE = re.compile(r'CURRENT_PLATFORM_VERSION\s*=\s*"([^"]+)"')

REQUIRED_WORKFLOWS = [
    "CI Foundation",
    "Python Lint And Tests",
    "Rust Lint And Tests",
    "Frontend Lint Test And Build",
    "Mobile Gradle Tests",
    "Contract Tests",
    "Playwright E2E",
    "Dependency Scan",
    "CodeQL",
    "Secret Scan",
    "Docker Build",
    "SBOM Generation",
    "Image Signing",
    "Staging Deployment",
]

REQUIRED_FILES = [
    ".github/workflows/ci-foundation.yml",
    ".github/workflows/python-lint-test.yml",
    ".github/workflows/rust-lint-test.yml",
    ".github/workflows/frontend-lint-test-build.yml",
    ".github/workflows/mobile-gradle-tests.yml",
    ".github/workflows/contract-tests.yml",
    ".github/workflows/playwright-e2e.yml",
    ".github/workflows/dependency-scan.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/secret-scan.yml",
    ".github/workflows/docker-build.yml",
    ".github/workflows/sbom-generation.yml",
    ".github/workflows/image-signing.yml",
    ".github/workflows/staging-deployment.yml",
    "tools/generate_sbom.py",
    "tools/generate_staging_deployment_plan.py",
    "backend/Dockerfile",
    "frontend-admin/Dockerfile",
    "contracts/COMPATIBILITY_MATRIX.md",
]


def validate_version(version: str) -> None:
    if not SEMVER_RE.fullmatch(version):
        raise ValueError(f"Release version must be semantic version text, got: {version}")


def validate_required_files() -> None:
    missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing release prerequisites: {', '.join(missing)}")


def read_frontend_version() -> str:
    package_json = json.loads((ROOT / "frontend-admin" / "package.json").read_text(encoding="utf-8"))
    return str(package_json["version"])


def read_backend_platform_version() -> str:
    services = (ROOT / "backend" / "apps" / "modules" / "services.py").read_text(encoding="utf-8")
    match = PLATFORM_VERSION_RE.search(services)
    if not match:
        raise ValueError("Could not find CURRENT_PLATFORM_VERSION in backend module services.")
    return match.group(1)


def read_rust_extension_version() -> str:
    cargo_toml = tomllib.loads((ROOT / "backend" / "rust_ext" / "Cargo.toml").read_text(encoding="utf-8"))
    return str(cargo_toml["package"]["version"])


def build_manifest(version: str) -> dict[str, Any]:
    validate_version(version)
    validate_required_files()
    return {
        "schema_version": "release-manifest.v1",
        "release_version": version,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": "dry-run",
        "repository": "YutakaX17/mobile-framework",
        "components": [
            {
                "name": "backend",
                "kind": "django-service",
                "version_source": "backend/apps/modules/services.py",
                "version": read_backend_platform_version(),
                "image": "mobile-framework-backend",
            },
            {
                "name": "frontend-admin",
                "kind": "vite-react-admin",
                "version_source": "frontend-admin/package.json",
                "version": read_frontend_version(),
                "image": "mobile-framework-frontend-admin",
            },
            {
                "name": "rust-extension",
                "kind": "pyo3-extension",
                "version_source": "backend/rust_ext/Cargo.toml",
                "version": read_rust_extension_version(),
            },
            {
                "name": "contracts",
                "kind": "json-schema",
                "schema_version": "v1",
                "compatibility_matrix": "contracts/COMPATIBILITY_MATRIX.md",
            },
            {
                "name": "mobile-runtime",
                "kind": "kotlin-multiplatform",
                "compatibility_range": "0.1.x",
            },
        ],
        "required_checks": REQUIRED_WORKFLOWS,
        "required_artifacts": [
            {
                "name": "release-manifest.json",
                "workflow": "Release",
                "path": "build/release/assets/release-manifest.json",
            },
            {
                "name": "mobile-framework-spdx-sbom",
                "workflow": "SBOM Generation",
                "path": "build/sbom/mobile-framework.spdx.json",
            },
            {
                "name": "mobile-framework.spdx.json",
                "workflow": "Release",
                "path": "build/release/assets/mobile-framework.spdx.json",
            },
            {
                "name": "backend-image-signing-bundle",
                "workflow": "Image Signing",
                "path": "build/image-signing/backend.sigstore.json",
            },
            {
                "name": "backend.digest",
                "workflow": "Release",
                "path": "build/release/assets/backend.digest",
            },
            {
                "name": "frontend-admin-image-signing-bundle",
                "workflow": "Image Signing",
                "path": "build/image-signing/frontend-admin.sigstore.json",
            },
            {
                "name": "frontend-admin.digest",
                "workflow": "Release",
                "path": "build/release/assets/frontend-admin.digest",
            },
            {
                "name": "staging-deployment-plan",
                "workflow": "Staging Deployment",
                "path": "build/deploy/staging-plan.json",
            },
            {
                "name": "staging-plan.json",
                "workflow": "Release",
                "path": "build/release/assets/staging-plan.json",
            },
            {
                "name": "contract-schema-bundle.zip",
                "workflow": "Release",
                "path": "build/release/assets/contract-schema-bundle.zip",
            },
            {
                "name": "generated-contract-types.zip",
                "workflow": "Release",
                "path": "build/release/assets/generated-contract-types.zip",
            },
            {
                "name": "openapi-schema-artifact.zip",
                "workflow": "Release",
                "path": "build/release/assets/openapi-schema-artifact.zip",
            },
            {
                "name": "schema-index.json",
                "workflow": "Release",
                "path": "build/release/assets/schema-index.json",
            },
            {
                "name": "field-ops-module-manifest.json",
                "workflow": "Release",
                "path": "build/release/assets/field-ops-module-manifest.json",
            },
            {
                "name": "demo-active-deployment-package.json",
                "workflow": "Release",
                "path": "build/release/assets/demo-active-deployment-package.json",
            },
            {
                "name": "release-notes.md",
                "workflow": "Release",
                "path": "build/release/assets/release-notes.md",
            },
            {
                "name": "asset-index.json",
                "workflow": "Release",
                "path": "build/release/assets/asset-index.json",
            },
        ],
        "release_steps": [
            "Validate semantic release version input",
            "Run foundation, backend, contract, frontend, mobile, and Rust validation",
            "Build backend and frontend container images",
            "Generate SPDX SBOM artifact",
            "Sign image digest artifacts with OIDC keyless signing",
            "Generate staging deployment plan artifact",
            "Bundle contracts, generated types, Field Ops plugin manifest, and demo package assets",
            "Create prerelease GitHub releases automatically for tag builds",
            "Keep stable release publishing disabled until the practical E2E MVP smoke test gate is complete",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a dry-run release manifest.")
    parser.add_argument("--version", required=True, help="Semantic release version to include in the manifest.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated release manifest for {args.version}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
