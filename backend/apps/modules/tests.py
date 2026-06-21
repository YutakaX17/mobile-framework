import json
from copy import deepcopy
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from apps.identity.models import PlatformPermission, PlatformRole, RolePermission, UserRoleAssignment
from apps.modules.models import ModuleRegistration, ModuleRegistrationStatus
from apps.tenants.models import Tenant


ROOT = Path(__file__).resolve().parents[3]
VALID_MANIFEST = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "module-manifest-core.json"
FIELD_OPS_MANIFEST = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "module-manifest-field-ops.json"


def load_valid_manifest() -> dict:
    with VALID_MANIFEST.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_field_ops_manifest() -> dict:
    with FIELD_OPS_MANIFEST.open(encoding="utf-8-sig") as handle:
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

    def test_built_in_field_ops_plugin_can_be_enabled_with_core_dependency(self):
        ModuleRegistration.from_manifest(load_valid_manifest()).save()
        manifest = load_field_ops_manifest()

        registration = ModuleRegistration.from_manifest(manifest)
        registration.status = ModuleRegistrationStatus.ENABLED
        registration.save()

        self.assertEqual(registration.module_id, "field_ops")
        self.assertEqual(registration.version, "0.1.0")
        self.assertEqual(registration.plugin_api_version, 0)
        self.assertEqual(registration.platform_min_version, "0.1.0")
        self.assertEqual(registration.platform_max_version, "0.1.0")
        self.assertEqual(registration.manifest["runtime_min_version"], "0.1.0")
        self.assertEqual(registration.manifest["runtime_max_version"], "0.1.0")
        self.assertEqual(registration.manifest["surfaces"]["mobile"]["sync_handlers"], ["field_ops_outbox"])
        self.assertEqual(registration.manifest["extensions"]["templates"]["forms"][0]["form_id"], "patient_intake")

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


class ModuleApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.user = get_user_model().objects.create_user(username="module-builder")
        self.grant_permissions(self.user, self.tenant, ["builder.app.manage"])
        self.client.force_login(self.user)
        ModuleRegistration.from_manifest(load_valid_manifest()).save()
        field_ops = ModuleRegistration.from_manifest(load_field_ops_manifest())
        field_ops.status = ModuleRegistrationStatus.ENABLED
        field_ops.save()

    def grant_permissions(self, user, tenant, permission_codes: list[str]) -> PlatformRole:
        role = PlatformRole.objects.create(tenant=tenant, slug=f"role-{user.username}", name="Module Builder")
        for code in permission_codes:
            permission, _created = PlatformPermission.objects.get_or_create(code=code, defaults={"name": code})
            RolePermission.objects.create(role=role, permission=permission)
        UserRoleAssignment.objects.create(tenant=tenant, user=user, role=role)
        return role

    def test_module_api_requires_authentication(self):
        response = Client().get("/api/modules/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_module_api_rejects_wrong_tenant(self):
        response = self.client.get("/api/modules/", HTTP_X_TENANT_SLUG="other")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")

    def test_module_api_rejects_missing_permission(self):
        user = get_user_model().objects.create_user(username="module-viewer")
        self.grant_permissions(user, self.tenant, ["core.view_dashboard"])
        client = Client()
        client.force_login(user)

        response = client.get("/api/modules/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")

    def test_module_list_returns_plugin_status(self):
        response = self.client.get("/api/modules/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 200)
        modules = response.json()["modules"]
        self.assertEqual([module["module_id"] for module in modules], ["core", "field_ops"])
        field_ops = modules[1]
        self.assertEqual(field_ops["status"], ModuleRegistrationStatus.ENABLED)
        self.assertTrue(field_ops["compatibility"]["is_compatible"])
        self.assertEqual(field_ops["templates"]["forms"][0]["form_id"], "patient_intake")

    def test_module_detail_returns_manifest(self):
        response = self.client.get("/api/modules/field_ops/", HTTP_X_TENANT_SLUG="demo")

        self.assertEqual(response.status_code, 200)
        module = response.json()["module"]
        self.assertEqual(module["module_id"], "field_ops")
        self.assertEqual(module["manifest"]["surfaces"]["mobile"]["sync_handlers"], ["field_ops_outbox"])
