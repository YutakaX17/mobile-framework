from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE.md",
    ".editorconfig",
    ".gitignore",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/epic.md",
    ".github/ISSUE_TEMPLATE/task.md",
    ".github/workflows/ci-foundation.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/contract-tests.yml",
    ".github/workflows/dependency-scan.yml",
    ".github/workflows/docker-build.yml",
    ".github/workflows/frontend-lint-test-build.yml",
    ".github/workflows/image-signing.yml",
    ".github/workflows/mobile-gradle-tests.yml",
    ".github/workflows/playwright-e2e.yml",
    ".github/workflows/python-lint-test.yml",
    ".github/workflows/release.yml",
    ".github/workflows/rust-lint-test.yml",
    ".github/workflows/sbom-generation.yml",
    ".github/workflows/secret-scan.yml",
    ".github/workflows/staging-deployment.yml",
    "implementation-notes/README.md",
    "implementation-notes/12-project-status.md",
    "docs/admin/ADMIN_USER_GUIDE.md",
    "docs/admin/APP_BUILDER_GUIDE.md",
    "docs/admin/FORM_BUILDER_GUIDE.md",
    "docs/admin/THEME_BUILDER_GUIDE.md",
    "docs/admin/WORKFLOW_BUILDER_GUIDE.md",
    "docs/adr/ADR-0000-template.md",
    "docs/developer/BACKEND_MODULES.md",
    "docs/developer/FRONTEND_MODULES.md",
    "docs/developer/GETTING_STARTED.md",
    "docs/mobile-runtime/RUNTIME_GUIDE.md",
    "docs/operations/DEPLOYMENT_AND_RELEASE_GUIDE.md",
    "docs/plugin-sdk/PLUGIN_SDK_GUIDE.md",
    "docs/site.json",
    "contracts/README.md",
    "contracts/SCHEMA_CONVENTIONS.md",
    "contracts/COMPATIBILITY_MATRIX.md",
    "contracts/validation_manifest.json",
    "contracts/validate_contracts.py",
    "contracts/requirements.txt",
    "backend/manage.py",
    "backend/config/settings/base.py",
    "backend/config/settings/database.py",
    "backend/config/settings/worker.py",
    "backend/config/settings/dev.py",
    "backend/config/settings/test.py",
    "backend/config/settings/prod.py",
    "backend/apps/__init__.py",
    "backend/apps/core/errors.py",
    "backend/apps/core/events.py",
    "backend/apps/core/jobs.py",
    "backend/apps/core/services.py",
    "backend/apps/core/views.py",
    "backend/apps/tenants/models.py",
    "backend/apps/tenants/migrations/0001_initial.py",
    "backend/apps/identity/models.py",
    "backend/apps/identity/migrations/0001_initial.py",
    "backend/apps/modules/models.py",
    "backend/apps/modules/services.py",
    "backend/apps/modules/migrations/0001_initial.py",
    "backend/apps/configurations/models.py",
    "backend/apps/configurations/services.py",
    "backend/apps/configurations/migrations/0001_initial.py",
    "backend/apps/audit/models.py",
    "backend/apps/audit/migrations/0001_initial.py",
    "backend/requirements.txt",
    "backend/.dockerignore",
    "backend/Dockerfile",
    "tools/generate_release_manifest.py",
    "tools/generate_sbom.py",
    "tools/generate_staging_deployment_plan.py",
    "tools/validate_backend.py",
    "tools/validate_docs_site.py",
    "tools/validate_python.py",
    "tools/validate_secret_scan.py",
    "tools/validate_workflow_builder.py",
    "infra/compose/docker-compose.yml",
    "frontend-admin/.dockerignore",
    "frontend-admin/Dockerfile",
    "frontend-admin/nginx.conf",
]

REQUIRED_DIRECTORIES = [
    "backend/apps",
    "frontend-admin/src",
    "mobile/shared",
    "contracts/schemas/v1",
    "contracts/fixtures/valid/v1",
    "contracts/fixtures/invalid/v1",
    "contracts/tests",
    "infra/compose",
    "docs/adr",
    "docs/developer",
]

REQUIRED_GITIGNORE_ENTRIES = [
    "__pycache__/",
    "node_modules/",
    ".env",
    ".venv/",
    ".pytest_cache/",
]

JSON_VALIDATION_ROOTS = [
    ".github",
    "contracts",
    "docs",
    "infra",
    "implementation-notes",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def require_path(relative_path: str, *, directory: bool = False) -> None:
    path = ROOT / relative_path
    if directory:
        if not path.is_dir():
            fail(f"Missing required directory: {relative_path}")
    else:
        if not path.is_file():
            fail(f"Missing required file: {relative_path}")
        if path.stat().st_size == 0:
            fail(f"Required file is empty: {relative_path}")


def validate_required_paths() -> None:
    for relative_path in REQUIRED_FILES:
        require_path(relative_path)
    for relative_path in REQUIRED_DIRECTORIES:
        require_path(relative_path, directory=True)


def validate_json_files() -> None:
    for root in JSON_VALIDATION_ROOTS:
        for path in sorted((ROOT / root).rglob("*.json")):
            try:
                with path.open(encoding="utf-8-sig") as handle:
                    json.load(handle)
            except json.JSONDecodeError as exc:
                relative = path.relative_to(ROOT)
                fail(f"Invalid JSON in {relative}: {exc}")


def validate_gitignore() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8-sig")
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry not in gitignore:
            fail(f".gitignore is missing required entry: {entry}")


def validate_workflow_replaced_placeholder() -> None:
    placeholder = ROOT / ".github" / "workflows" / "ci-placeholder.yml"
    if placeholder.exists():
        fail("Placeholder workflow still exists: .github/workflows/ci-placeholder.yml")
    workflow = (ROOT / ".github" / "workflows" / "ci-foundation.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: CI Foundation",
        "python tools/validate_foundation.py",
        "python contracts/validate_contracts.py",
        "python tools/validate_backend.py",
        "python tools/validate_workflow_builder.py",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"ci-foundation.yml is missing: {snippet}")


def validate_python_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "python-lint-test.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Python Lint And Tests",
        "python tools/validate_python.py",
        "python contracts/validate_contracts.py",
        "python tools/validate_backend.py",
        "python tools/validate_workflow_builder.py",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"python-lint-test.yml is missing: {snippet}")


def validate_rust_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "rust-lint-test.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Rust Lint And Tests",
        "rustc --version",
        "cargo --version",
        "python tools/validate_rust_ext.py --include-python-wrapper",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"rust-lint-test.yml is missing: {snippet}")


def validate_frontend_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "frontend-lint-test-build.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Frontend Lint Test And Build",
        'node-version: "24"',
        "cache-dependency-path: frontend-admin/package-lock.json",
        "npm ci",
        "npx playwright install --with-deps chromium",
        "python tools/validate_frontend_admin.py",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"frontend-lint-test-build.yml is missing: {snippet}")


def validate_mobile_gradle_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "mobile-gradle-tests.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Mobile Gradle Tests",
        "actions/setup-java@v4",
        "android-actions/setup-android@v3",
        "gradle/actions/setup-gradle@v4",
        'gradle-version: "9.5.0"',
        "python tools/validate_mobile.py",
        "python tools/validate_mobile_tests.py",
        "gradle :shared:desktopTest :composeApp:desktopTest --stacktrace",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"mobile-gradle-tests.yml is missing: {snippet}")


def validate_contract_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "contract-tests.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Contract Tests",
        'python-version: "3.11"',
        "python -m pip install -r contracts/requirements.txt",
        "python contracts/generate_types.py --target typescript --check",
        "python contracts/generate_types.py --target python --check",
        "python contracts/generate_types.py --target kotlin --check",
        "python contracts/validate_contracts.py",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"contract-tests.yml is missing: {snippet}")


def validate_playwright_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "playwright-e2e.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Playwright E2E",
        'node-version: "24"',
        "cache-dependency-path: frontend-admin/package-lock.json",
        "npm ci",
        "npx playwright install --with-deps chromium",
        "npm run build",
        "npm run smoke",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"playwright-e2e.yml is missing: {snippet}")


def validate_dependency_scan_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "dependency-scan.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Dependency Scan",
        "pull_request:",
        "pull-requests: read",
        "actions/dependency-review-action@v4",
        "fail-on-severity: high",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"dependency-scan.yml is missing: {snippet}")


def validate_codeql_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: CodeQL",
        "security-events: write",
        "github/codeql-action/init@v4",
        "github/codeql-action/analyze@v4",
        "language: python",
        "language: javascript-typescript",
        "build-mode: none",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"codeql.yml is missing: {snippet}")


def validate_secret_scan_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "secret-scan.yml").read_text(encoding="utf-8-sig")
    script = (ROOT / "tools" / "validate_secret_scan.py").read_text(encoding="utf-8-sig")
    required_workflow_snippets = [
        "name: Secret Scan",
        "pull_request:",
        'python-version: "3.11"',
        "python tools/validate_secret_scan.py",
    ]
    required_script_snippets = [
        "SECRET_PATTERNS",
        "git",
        "ls-files",
        "private-key-block",
        "long-secret-assignment",
    ]
    for snippet in required_workflow_snippets:
        if snippet not in workflow:
            fail(f"secret-scan.yml is missing: {snippet}")
    for snippet in required_script_snippets:
        if snippet not in script:
            fail(f"validate_secret_scan.py is missing: {snippet}")


def validate_docker_build_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "docker-build.yml").read_text(encoding="utf-8-sig")
    backend_dockerfile = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8-sig")
    frontend_dockerfile = (ROOT / "frontend-admin" / "Dockerfile").read_text(encoding="utf-8-sig")
    required_workflow_snippets = [
        "name: Docker Build",
        "docker build --tag",
        "mobile-framework-backend",
        "mobile-framework-frontend-admin",
        "${{ matrix.context }}",
    ]
    required_backend_snippets = [
        "FROM python:3.13-slim",
        "COPY requirements.txt",
        "python -m pip install --no-cache-dir -r requirements.txt",
        'CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]',
    ]
    required_frontend_snippets = [
        "FROM node:24-alpine AS build",
        "npm ci",
        "npm run build",
        "FROM nginx:1.27-alpine",
        "COPY nginx.conf /etc/nginx/conf.d/default.conf",
    ]
    for snippet in required_workflow_snippets:
        if snippet not in workflow:
            fail(f"docker-build.yml is missing: {snippet}")
    for snippet in required_backend_snippets:
        if snippet not in backend_dockerfile:
            fail(f"backend/Dockerfile is missing: {snippet}")
    for snippet in required_frontend_snippets:
        if snippet not in frontend_dockerfile:
            fail(f"frontend-admin/Dockerfile is missing: {snippet}")


def validate_docs_site() -> None:
    config = json.loads((ROOT / "docs" / "site.json").read_text(encoding="utf-8-sig"))
    script = (ROOT / "tools" / "validate_docs_site.py").read_text(encoding="utf-8-sig")
    required_nav_paths = [
        "README.md",
        "product/README.md",
        "developer/README.md",
        "admin/README.md",
        "mobile-runtime/README.md",
        "plugin-sdk/README.md",
        "operations/README.md",
        "adr/README.md",
    ]
    nav_paths = {entry.get("path") for entry in config.get("nav", []) if isinstance(entry, dict)}
    for path in required_nav_paths:
        if path not in nav_paths:
            fail(f"docs/site.json is missing required nav path: {path}")
    required_script_snippets = [
        "Docs site validation",
        "admin/ADMIN_USER_GUIDE.md",
        "admin/APP_BUILDER_GUIDE.md",
        "admin/FORM_BUILDER_GUIDE.md",
        "admin/THEME_BUILDER_GUIDE.md",
        "admin/WORKFLOW_BUILDER_GUIDE.md",
        "developer/BACKEND_MODULES.md",
        "developer/FRONTEND_MODULES.md",
        "mobile-runtime/RUNTIME_GUIDE.md",
        "operations/DEPLOYMENT_AND_RELEASE_GUIDE.md",
        "plugin-sdk/PLUGIN_SDK_GUIDE.md",
        "REQUIRED_DOCUMENT_PATHS",
        "REQUIRED_README_LINKS",
        "developer/GETTING_STARTED.md",
        "REQUIRED_NAV_PATHS",
        "docs/site.json",
        "mobile-runtime/README.md",
        "plugin-sdk/README.md",
    ]
    for snippet in required_script_snippets:
        if snippet not in script:
            fail(f"validate_docs_site.py is missing: {snippet}")


def validate_sbom_generation_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "sbom-generation.yml").read_text(encoding="utf-8-sig")
    script = (ROOT / "tools" / "generate_sbom.py").read_text(encoding="utf-8-sig")
    required_workflow_snippets = [
        "name: SBOM Generation",
        'python-version: "3.11"',
        "python tools/generate_sbom.py --output build/sbom/mobile-framework.spdx.json",
        "actions/upload-artifact@v4",
        "mobile-framework-spdx-sbom",
    ]
    required_script_snippets = [
        "spdxVersion",
        "SPDX-2.3",
        '"backend"',
        '"requirements.txt"',
        '"contracts"',
        "frontend-admin",
        "package-lock.json",
    ]
    for snippet in required_workflow_snippets:
        if snippet not in workflow:
            fail(f"sbom-generation.yml is missing: {snippet}")
    for snippet in required_script_snippets:
        if snippet not in script:
            fail(f"generate_sbom.py is missing: {snippet}")


def validate_image_signing_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "image-signing.yml").read_text(encoding="utf-8-sig")
    required_snippets = [
        "name: Image Signing",
        "id-token: write",
        "docker build --tag",
        "docker image inspect --format",
        "sigstore/cosign-installer@v3",
        "cosign sign-blob",
        "actions/upload-artifact@v4",
        "mobile-framework-backend",
        "mobile-framework-frontend-admin",
    ]
    for snippet in required_snippets:
        if snippet not in workflow:
            fail(f"image-signing.yml is missing: {snippet}")


def validate_staging_deployment_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "staging-deployment.yml").read_text(encoding="utf-8-sig")
    script = (ROOT / "tools" / "generate_staging_deployment_plan.py").read_text(encoding="utf-8-sig")
    required_workflow_snippets = [
        "name: Staging Deployment",
        "workflow_dispatch:",
        "environment:",
        "name: staging",
        "python tools/generate_staging_deployment_plan.py --output build/deploy/staging-plan.json",
        "actions/upload-artifact@v4",
        "staging-deployment-plan",
    ]
    required_script_snippets = [
        "staging-deployment-plan.v1",
        "Docker Build",
        "Image Signing",
        "SBOM Generation",
        "mobile-framework-backend",
        "mobile-framework-frontend-admin",
    ]
    for snippet in required_workflow_snippets:
        if snippet not in workflow:
            fail(f"staging-deployment.yml is missing: {snippet}")
    for snippet in required_script_snippets:
        if snippet not in script:
            fail(f"generate_staging_deployment_plan.py is missing: {snippet}")


def validate_release_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8-sig")
    script = (ROOT / "tools" / "generate_release_manifest.py").read_text(encoding="utf-8-sig")
    required_workflow_snippets = [
        "name: Release",
        "workflow_dispatch:",
        "version:",
        "RELEASE_VERSION:",
        "python tools/generate_release_manifest.py --version",
        "actions/upload-artifact@v4",
        "release-manifest",
    ]
    required_script_snippets = [
        "release-manifest.v1",
        "release_version",
        "Docker Build",
        "SBOM Generation",
        "Image Signing",
        "Staging Deployment",
        "mobile-framework-spdx-sbom",
        "backend-image-signing-bundle",
        "frontend-admin-image-signing-bundle",
    ]
    for snippet in required_workflow_snippets:
        if snippet not in workflow:
            fail(f"release.yml is missing: {snippet}")
    for snippet in required_script_snippets:
        if snippet not in script:
            fail(f"generate_release_manifest.py is missing: {snippet}")


def main() -> int:
    checks = [
        validate_required_paths,
        validate_json_files,
        validate_gitignore,
        validate_codeql_workflow,
        validate_contract_workflow,
        validate_dependency_scan_workflow,
        validate_docker_build_workflow,
        validate_docs_site,
        validate_workflow_replaced_placeholder,
        validate_frontend_workflow,
        validate_image_signing_workflow,
        validate_mobile_gradle_workflow,
        validate_playwright_workflow,
        validate_python_workflow,
        validate_release_workflow,
        validate_rust_workflow,
        validate_sbom_generation_workflow,
        validate_secret_scan_workflow,
        validate_staging_deployment_workflow,
    ]
    try:
        for check in checks:
            check()
    except AssertionError as exc:
        print(f"Foundation validation failed: {exc}", file=sys.stderr)
        return 1
    print("Foundation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
