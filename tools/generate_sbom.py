from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "sbom" / "mobile-framework.spdx.json"

PYTHON_MANIFESTS = [
    ROOT / "backend" / "requirements.txt",
    ROOT / "contracts" / "requirements.txt",
]
NPM_LOCKFILES = [
    ROOT / "frontend-admin" / "package-lock.json",
]


def spdx_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9.-]+", "-", value).strip("-")
    return f"SPDXRef-{normalized or 'package'}"


def parse_python_requirement(line: str) -> tuple[str, str] | None:
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#") or cleaned.startswith("-"):
        return None
    name = re.split(r"[<>=!~;\[]", cleaned, maxsplit=1)[0].strip()
    if not name:
        return None
    specifier = cleaned[len(name) :].strip() or "NOASSERTION"
    return name, specifier


def python_packages() -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for manifest in PYTHON_MANIFESTS:
        manifest_name = manifest.relative_to(ROOT).as_posix()
        for line in manifest.read_text(encoding="utf-8-sig").splitlines():
            parsed = parse_python_requirement(line)
            if parsed is None:
                continue
            name, specifier = parsed
            package_key = f"python:{manifest_name}:{name}"
            packages.append(
                {
                    "SPDXID": spdx_id(package_key),
                    "name": name,
                    "versionInfo": specifier,
                    "downloadLocation": "NOASSERTION",
                    "filesAnalyzed": False,
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": "NOASSERTION",
                    "supplier": "NOASSERTION",
                    "externalRefs": [
                        {
                            "referenceCategory": "PACKAGE-MANAGER",
                            "referenceType": "purl",
                            "referenceLocator": f"pkg:pypi/{name}",
                        }
                    ],
                }
            )
    return packages


def package_name_from_lock_path(path: str, package: dict[str, Any]) -> str:
    if package.get("name"):
        return str(package["name"])
    if path.startswith("node_modules/"):
        return path.removeprefix("node_modules/")
    return path or "frontend-admin"


def npm_packages() -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for lockfile in NPM_LOCKFILES:
        lock = json.loads(lockfile.read_text(encoding="utf-8-sig"))
        packages_by_path = lock.get("packages", {})
        if not isinstance(packages_by_path, dict):
            continue
        for package_path, package in sorted(packages_by_path.items()):
            if package_path == "" or not isinstance(package, dict):
                continue
            name = package_name_from_lock_path(package_path, package)
            version = str(package.get("version", "NOASSERTION"))
            license_declared = package.get("license")
            if not isinstance(license_declared, str) or not license_declared:
                license_declared = "NOASSERTION"
            package_key = f"npm:{lockfile.relative_to(ROOT).as_posix()}:{name}"
            packages.append(
                {
                    "SPDXID": spdx_id(package_key),
                    "name": name,
                    "versionInfo": version,
                    "downloadLocation": str(package.get("resolved", "NOASSERTION")),
                    "filesAnalyzed": False,
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": license_declared,
                    "supplier": "NOASSERTION",
                    "externalRefs": [
                        {
                            "referenceCategory": "PACKAGE-MANAGER",
                            "referenceType": "purl",
                            "referenceLocator": f"pkg:npm/{name}@{version}",
                        }
                    ],
                }
            )
    return packages


def build_document() -> dict[str, Any]:
    packages = python_packages() + npm_packages()
    relationships = [
        {
            "spdxElementId": "SPDXRef-DOCUMENT",
            "relationshipType": "DESCRIBES",
            "relatedSpdxElement": package["SPDXID"],
        }
        for package in packages
    ]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "mobile-framework",
        "documentNamespace": "https://github.com/YutakaX17/mobile-framework/sbom/mobile-framework",
        "creationInfo": {
            "created": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "creators": ["Tool: tools/generate_sbom.py"],
        },
        "packages": packages,
        "relationships": relationships,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a baseline SPDX JSON SBOM.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = build_document()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated SBOM with {len(document['packages'])} packages: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
