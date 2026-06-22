from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from generate_release_manifest import validate_version


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "build" / "release" / "assets"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def zip_paths(output: Path, paths: list[Path]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_file():
                try:
                    archive_path = path.relative_to(ROOT).as_posix()
                except ValueError:
                    archive_path = path.name
                archive.write(path, archive_path)
            elif path.is_dir():
                for child in sorted(path.rglob("*")):
                    if child.is_file():
                        archive.write(child, child.relative_to(ROOT).as_posix())


def copy_asset(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Missing release asset source: {source.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def write_schema_index(output: Path) -> None:
    schemas = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "contracts" / "schemas").rglob("*.json"))
    payload = {
        "schema_version": "release-schema-index.v1",
        "generated_at": utc_now(),
        "schemas": schemas,
        "openapi": {
            "available": False,
            "notes": "OpenAPI export is not available yet; JSON schema bundles are the current contract artifact.",
        },
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_release_notes(version: str, output: Path) -> None:
    prerelease = "-" in version
    stability = "prerelease" if prerelease else "stable candidate"
    output.write_text(
        "\n".join(
            [
                f"# Mobile Framework v{version}",
                "",
                f"This is a {stability} platform release artifact set.",
                "",
                "## Included Assets",
                "",
                "- `release-manifest.json`: release checks, components, and expected evidence.",
                "- `mobile-framework.spdx.json`: SPDX SBOM.",
                "- `staging-plan.json`: dry-run staging deployment plan.",
                "- `contract-schema-bundle.zip`: JSON schema contracts.",
                "- `generated-contract-types.zip`: generated TypeScript, Python, and Kotlin contract types.",
                "- `openapi-schema-artifact.zip`: current schema index and OpenAPI placeholder.",
                "- `field-ops-module-manifest.json`: built-in Field Ops module manifest.",
                "- `demo-active-deployment-package.json`: deterministic demo package payload fixture.",
                "",
                "Stable releases must not be promoted until the practical end-to-end MVP smoke test has passed.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_assets(
    *,
    version: str,
    output_dir: Path,
    release_manifest: Path,
    sbom: Path,
    staging_plan: Path,
) -> dict[str, Any]:
    validate_version(version)
    output_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, str]] = []

    copies = [
        (release_manifest, "release-manifest.json", "Release manifest and evidence checklist."),
        (sbom, "mobile-framework.spdx.json", "SPDX software bill of materials."),
        (staging_plan, "staging-plan.json", "Dry-run staging deployment plan."),
        (
            ROOT / "contracts" / "fixtures" / "valid" / "v1" / "module-manifest-field-ops.json",
            "field-ops-module-manifest.json",
            "Built-in Field Ops plugin/module manifest.",
        ),
        (
            ROOT / "contracts" / "fixtures" / "valid" / "v1" / "deployment-package-field-ops.json",
            "demo-active-deployment-package.json",
            "Deterministic demo deployment package payload.",
        ),
    ]
    for source, name, description in copies:
        destination = output_dir / name
        copy_asset(source, destination)
        assets.append({"name": name, "path": destination.as_posix(), "description": description})

    schema_bundle = output_dir / "contract-schema-bundle.zip"
    zip_paths(
        schema_bundle,
        [
            ROOT / "contracts" / "schemas",
            ROOT / "contracts" / "validation_manifest.json",
            ROOT / "contracts" / "COMPATIBILITY_MATRIX.md",
        ],
    )
    assets.append(
        {
            "name": schema_bundle.name,
            "path": schema_bundle.as_posix(),
            "description": "JSON schema contract bundle.",
        }
    )

    generated_types = output_dir / "generated-contract-types.zip"
    zip_paths(generated_types, [ROOT / "contracts" / "generated"])
    assets.append(
        {
            "name": generated_types.name,
            "path": generated_types.as_posix(),
            "description": "Generated contract type declarations.",
        }
    )

    schema_index = output_dir / "schema-index.json"
    write_schema_index(schema_index)
    assets.append(
        {
            "name": schema_index.name,
            "path": schema_index.as_posix(),
            "description": "Schema and OpenAPI availability index.",
        }
    )
    openapi_artifact = output_dir / "openapi-schema-artifact.zip"
    zip_paths(openapi_artifact, [schema_index, ROOT / "contracts" / "openapi" / "README.md"])
    assets.append(
        {
            "name": openapi_artifact.name,
            "path": openapi_artifact.as_posix(),
            "description": "Schema index and OpenAPI availability artifact.",
        }
    )

    notes = output_dir / "release-notes.md"
    write_release_notes(version, notes)
    assets.append({"name": notes.name, "path": notes.as_posix(), "description": "Release notes draft."})

    index_path = output_dir / "asset-index.json"
    assets.append(
        {
            "name": index_path.name,
            "path": index_path.as_posix(),
            "description": "Machine-readable index of release assets.",
        }
    )
    index = {
        "schema_version": "release-assets.v1",
        "release_version": version,
        "generated_at": utc_now(),
        "assets": assets,
    }
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic release asset bundle.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--staging-plan", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index = build_assets(
        version=args.version,
        output_dir=args.output_dir,
        release_manifest=args.release_manifest,
        sbom=args.sbom,
        staging_plan=args.staging_plan,
    )
    print(f"Generated {len(index['assets'])} release assets in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
