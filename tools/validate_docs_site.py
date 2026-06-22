from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
SITE_CONFIG = DOCS_ROOT / "site.json"

REQUIRED_NAV_PATHS = [
    "README.md",
    "product/README.md",
    "developer/README.md",
    "admin/README.md",
    "mobile-runtime/README.md",
    "plugin-sdk/README.md",
    "operations/README.md",
    "adr/README.md",
]

REQUIRED_DOCUMENT_PATHS = [
    "admin/ADMIN_USER_GUIDE.md",
    "admin/APP_BUILDER_GUIDE.md",
    "admin/FORM_BUILDER_GUIDE.md",
    "admin/THEME_BUILDER_GUIDE.md",
    "admin/WORKFLOW_BUILDER_GUIDE.md",
    "developer/BACKEND_MODULES.md",
    "developer/FRONTEND_MODULES.md",
    "developer/GETTING_STARTED.md",
    "operations/CHANGELOG_PROCESS.md",
    "mobile-runtime/RUNTIME_GUIDE.md",
    "operations/BACKUP_RESTORE_GUIDE.md",
    "operations/DEPLOYMENT_AND_RELEASE_GUIDE.md",
    "operations/PRACTICAL_MVP_SMOKE_TEST.md",
    "operations/UPGRADE_GUIDE.md",
    "plugin-sdk/PLUGIN_SDK_GUIDE.md",
]

REQUIRED_README_LINKS = {
    "admin/README.md": [
        "ADMIN_USER_GUIDE.md",
        "APP_BUILDER_GUIDE.md",
        "FORM_BUILDER_GUIDE.md",
        "THEME_BUILDER_GUIDE.md",
        "WORKFLOW_BUILDER_GUIDE.md",
    ],
    "developer/README.md": [
        "BACKEND_MODULES.md",
        "FRONTEND_MODULES.md",
        "GETTING_STARTED.md",
        "LOCAL_SETUP.md",
    ],
    "mobile-runtime/README.md": [
        "RUNTIME_GUIDE.md",
    ],
    "operations/README.md": [
        "BACKUP_RESTORE_GUIDE.md",
        "CHANGELOG_PROCESS.md",
        "DEPLOYMENT_AND_RELEASE_GUIDE.md",
        "PRACTICAL_MVP_SMOKE_TEST.md",
        "REPOSITORY_PROTECTION.md",
        "UPGRADE_GUIDE.md",
    ],
    "plugin-sdk/README.md": [
        "PLUGIN_SDK_GUIDE.md",
    ],
}


def fail(message: str) -> None:
    raise AssertionError(message)


def load_site_config() -> dict[str, Any]:
    if not SITE_CONFIG.is_file():
        fail("Missing docs site configuration: docs/site.json")
    try:
        payload = json.loads(SITE_CONFIG.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in docs/site.json: {exc}")
    if not isinstance(payload, dict):
        fail("docs/site.json must contain a JSON object.")
    return payload


def validate_nav_entry(entry: Any, index: int) -> tuple[str, str]:
    if not isinstance(entry, dict):
        fail(f"docs/site.json nav entry {index} must be an object.")
    title = entry.get("title")
    path = entry.get("path")
    if not isinstance(title, str) or not title.strip():
        fail(f"docs/site.json nav entry {index} is missing a title.")
    if not isinstance(path, str) or not path.strip():
        fail(f"docs/site.json nav entry {index} is missing a path.")
    if Path(path).is_absolute() or ".." in Path(path).parts:
        fail(f"docs/site.json nav path is not allowed: {path}")
    target = DOCS_ROOT / path
    if not target.is_file():
        fail(f"docs/site.json nav target is missing: docs/{path}")
    if target.suffix.lower() != ".md":
        fail(f"docs/site.json nav target must be Markdown: docs/{path}")
    return title, path


def validate_site_config() -> None:
    payload = load_site_config()
    site_name = payload.get("site_name")
    if not isinstance(site_name, str) or not site_name.strip():
        fail("docs/site.json is missing a non-empty site_name.")
    nav = payload.get("nav")
    if not isinstance(nav, list) or not nav:
        fail("docs/site.json is missing a non-empty nav list.")

    seen_titles: set[str] = set()
    seen_paths: set[str] = set()
    for index, entry in enumerate(nav, start=1):
        title, path = validate_nav_entry(entry, index)
        if title in seen_titles:
            fail(f"docs/site.json has duplicate nav title: {title}")
        if path in seen_paths:
            fail(f"docs/site.json has duplicate nav path: docs/{path}")
        seen_titles.add(title)
        seen_paths.add(path)

    for required_path in REQUIRED_NAV_PATHS:
        if required_path not in seen_paths:
            fail(f"docs/site.json is missing required nav path: docs/{required_path}")


def validate_required_documents() -> None:
    for required_path in REQUIRED_DOCUMENT_PATHS:
        target = DOCS_ROOT / required_path
        if not target.is_file():
            fail(f"Missing required docs page: docs/{required_path}")
        if target.stat().st_size == 0:
            fail(f"Required docs page is empty: docs/{required_path}")


def validate_readme_links() -> None:
    for readme_path, links in REQUIRED_README_LINKS.items():
        readme = DOCS_ROOT / readme_path
        if not readme.is_file():
            fail(f"Missing docs README: docs/{readme_path}")
        content = readme.read_text(encoding="utf-8-sig")
        for link in links:
            if f"]({link})" not in content:
                fail(f"docs/{readme_path} is missing link to {link}")


def main() -> int:
    try:
        validate_site_config()
        validate_required_documents()
        validate_readme_links()
    except AssertionError as exc:
        print(f"Docs site validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "Docs site validation passed for "
        f"{len(REQUIRED_NAV_PATHS)} nav pages and {len(REQUIRED_DOCUMENT_PATHS)} required docs pages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
