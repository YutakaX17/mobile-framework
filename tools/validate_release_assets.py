from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from generate_release_assets import build_assets
from generate_release_manifest import build_manifest
from generate_sbom import build_document
from generate_staging_deployment_plan import build_plan


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ASSETS = {
    "release-manifest.json",
    "mobile-framework.spdx.json",
    "staging-plan.json",
    "contract-schema-bundle.zip",
    "generated-contract-types.zip",
    "openapi-schema-artifact.zip",
    "schema-index.json",
    "field-ops-module-manifest.json",
    "demo-active-deployment-package.json",
    "release-notes.md",
    "asset-index.json",
}


def require_contains(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} must contain `{text}`")


def validate_release_workflow() -> None:
    workflow = ROOT / ".github" / "workflows" / "release.yml"
    require_contains(workflow, "tags:")
    require_contains(workflow, "v*")
    require_contains(workflow, "workflow_dispatch:")
    require_contains(workflow, "generate_release_assets.py")
    require_contains(workflow, "gh release create")
    require_contains(workflow, "ALLOW_STABLE_RELEASE")


def validate_manifest() -> None:
    manifest = build_manifest("0.1.0-rc.1")
    artifact_names = {artifact["name"] for artifact in manifest["required_artifacts"]}
    for required in REQUIRED_ASSETS:
        if required not in artifact_names:
            raise AssertionError(f"Release manifest missing required artifact: {required}")
    if "Mobile Gradle Tests" not in manifest["required_checks"]:
        raise AssertionError("Release manifest must require Mobile Gradle Tests.")


def validate_assets() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="mobile-framework-release-assets-"))
    try:
        release_manifest = temp_root / "release-manifest.json"
        release_manifest.write_text(json.dumps(build_manifest("0.1.0-rc.1"), indent=2), encoding="utf-8")
        sbom = temp_root / "mobile-framework.spdx.json"
        sbom.write_text(json.dumps(build_document(), indent=2), encoding="utf-8")
        staging_plan = temp_root / "staging-plan.json"
        staging_plan.write_text(json.dumps(build_plan(), indent=2), encoding="utf-8")
        output_dir = temp_root / "assets"

        index = build_assets(
            version="0.1.0-rc.1",
            output_dir=output_dir,
            release_manifest=release_manifest,
            sbom=sbom,
            staging_plan=staging_plan,
        )
        asset_names = {asset["name"] for asset in index["assets"]}
        missing = REQUIRED_ASSETS - asset_names
        if missing:
            raise AssertionError(f"Missing generated release assets: {', '.join(sorted(missing))}")
        for asset in index["assets"]:
            if not Path(asset["path"]).is_file():
                raise AssertionError(f"Generated asset path does not exist: {asset['path']}")
    finally:
        shutil.rmtree(temp_root)


def main() -> int:
    validate_release_workflow()
    validate_manifest()
    validate_assets()
    print("Release asset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
