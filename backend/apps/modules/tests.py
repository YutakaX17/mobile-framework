import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.modules.models import ModuleRegistration, ModuleRegistrationStatus


ROOT = Path(__file__).resolve().parents[3]
VALID_MANIFEST = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "module-manifest-core.json"


def load_valid_manifest() -> dict:
    with VALID_MANIFEST.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class ModuleRegistrationTests(TestCase):
    def test_registration_can_be_created_from_valid_manifest(self):
        manifest = load_valid_manifest()

        registration = ModuleRegistration.from_manifest(manifest)
        registration.save()

        self.assertEqual(registration.module_id, manifest["module_id"])
        self.assertEqual(registration.version, manifest["version"])
        self.assertEqual(registration.status, ModuleRegistrationStatus.REGISTERED)
        self.assertEqual(str(registration), f"{manifest['module_id']}@{manifest['version']}")

    def test_invalid_manifest_is_rejected(self):
        manifest = load_valid_manifest()
        manifest.pop("module_id")

        registration = ModuleRegistration(
            module_id="core",
            name=manifest["name"],
            version=manifest["version"],
            schema_version=manifest["schema_version"],
            plugin_api_version=manifest["plugin_api_version"],
            platform_min_version=manifest["platform_min_version"],
            manifest=manifest,
        )

        with self.assertRaises(ValidationError):
            registration.full_clean()

    def test_model_fields_must_match_manifest(self):
        manifest = load_valid_manifest()
        registration = ModuleRegistration.from_manifest(deepcopy(manifest))
        registration.module_id = "different"

        with self.assertRaises(ValidationError):
            registration.full_clean()

    def test_module_version_is_unique(self):
        manifest = load_valid_manifest()
        ModuleRegistration.from_manifest(manifest).save()

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_platform_compatible_module_can_be_registered(self):
        manifest = load_valid_manifest()
        manifest["platform_max_version"] = "0.1.0"

        registration = ModuleRegistration.from_manifest(manifest)
        registration.save()

        self.assertEqual(registration.platform_min_version, "0.1.0")
        self.assertEqual(registration.platform_max_version, "0.1.0")

    def test_missing_platform_max_version_does_not_block_registration(self):
        manifest = load_valid_manifest()
        manifest.pop("platform_max_version", None)

        registration = ModuleRegistration.from_manifest(manifest)
        registration.save()

        self.assertEqual(registration.platform_max_version, "")

    def test_invalid_platform_min_version_is_rejected(self):
        manifest = load_valid_manifest()
        manifest["platform_min_version"] = "latest"

        registration = ModuleRegistration(
            module_id=manifest["module_id"],
            name=manifest["name"],
            version=manifest["version"],
            schema_version=manifest["schema_version"],
            plugin_api_version=manifest["plugin_api_version"],
            platform_min_version=manifest["platform_min_version"],
            manifest=manifest,
        )

        with self.assertRaises(ValidationError):
            registration.full_clean()

    def test_newer_platform_min_version_is_rejected(self):
        manifest = load_valid_manifest()
        manifest["platform_min_version"] = "0.2.0"

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_older_platform_max_version_is_rejected(self):
        manifest = load_valid_manifest()
        manifest["platform_max_version"] = "0.0.9"

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_inconsistent_platform_range_is_rejected(self):
        manifest = load_valid_manifest()
        manifest["platform_min_version"] = "0.2.0"
        manifest["platform_max_version"] = "0.1.0"

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_required_dependency_can_be_satisfied_by_registered_module(self):
        dependency_manifest = load_valid_manifest()
        ModuleRegistration.from_manifest(dependency_manifest).save()
        manifest = load_valid_manifest()
        manifest["module_id"] = "reports"
        manifest["name"] = "Reports"
        manifest["dependencies"] = [
            {
                "module_id": "core",
                "version_constraint": ">=0.1.0,<1.0.0",
            }
        ]

        registration = ModuleRegistration.from_manifest(manifest)
        registration.save()

        self.assertEqual(registration.module_id, "reports")

    def test_missing_required_dependency_is_rejected(self):
        manifest = load_valid_manifest()
        manifest["module_id"] = "reports"
        manifest["name"] = "Reports"
        manifest["dependencies"] = [
            {
                "module_id": "core",
                "version_constraint": ">=0.1.0",
            }
        ]

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_missing_optional_dependency_does_not_block_registration(self):
        manifest = load_valid_manifest()
        manifest["module_id"] = "reports"
        manifest["name"] = "Reports"
        manifest["dependencies"] = [
            {
                "module_id": "analytics",
                "version_constraint": ">=0.1.0",
                "optional": True,
            }
        ]

        registration = ModuleRegistration.from_manifest(manifest)
        registration.save()

        self.assertEqual(registration.module_id, "reports")

    def test_installed_optional_dependency_must_satisfy_constraint(self):
        dependency_manifest = load_valid_manifest()
        ModuleRegistration.from_manifest(dependency_manifest).save()
        manifest = load_valid_manifest()
        manifest["module_id"] = "reports"
        manifest["name"] = "Reports"
        manifest["dependencies"] = [
            {
                "module_id": "core",
                "version_constraint": ">=1.0.0",
                "optional": True,
            }
        ]

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_self_dependency_is_rejected(self):
        manifest = load_valid_manifest()
        manifest["dependencies"] = [
            {
                "module_id": "core",
                "version_constraint": ">=0.1.0",
            }
        ]

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()

    def test_duplicate_dependency_module_ids_are_rejected(self):
        manifest = load_valid_manifest()
        manifest["module_id"] = "reports"
        manifest["name"] = "Reports"
        manifest["dependencies"] = [
            {
                "module_id": "core",
                "version_constraint": ">=0.1.0",
            },
            {
                "module_id": "core",
                "version_constraint": "<1.0.0",
            },
        ]

        with self.assertRaises(ValidationError):
            ModuleRegistration.from_manifest(manifest).save()
