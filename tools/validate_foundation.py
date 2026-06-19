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
    ".github/workflows/contract-tests.yml",
    ".github/workflows/frontend-lint-test-build.yml",
    ".github/workflows/mobile-gradle-tests.yml",
    ".github/workflows/python-lint-test.yml",
    ".github/workflows/rust-lint-test.yml",
    "implementation-notes/README.md",
    "implementation-notes/12-project-status.md",
    "docs/adr/ADR-0000-template.md",
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
    "tools/validate_backend.py",
    "tools/validate_python.py",
    "tools/validate_workflow_builder.py",
    "infra/compose/docker-compose.yml",
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


def main() -> int:
    checks = [
        validate_required_paths,
        validate_json_files,
        validate_gitignore,
        validate_contract_workflow,
        validate_workflow_replaced_placeholder,
        validate_frontend_workflow,
        validate_mobile_gradle_workflow,
        validate_python_workflow,
        validate_rust_workflow,
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
