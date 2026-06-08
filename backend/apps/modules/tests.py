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
