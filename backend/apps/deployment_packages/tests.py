import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.app_builder.models import AppDefinition, AppRevision, AppRevisionStatus
from apps.deployment_packages.models import DeploymentChannel, DeploymentPackage, DeploymentPackageStatus
from apps.deployment_packages.services import (
    activate_deployment_package,
    active_deployment_package,
    compile_deployment_package,
    compile_deployment_package_payload,
    create_default_release_channels,
    package_hash,
    release_channel_names,
    rollback_deployment_package,
    sign_deployment_package_payload,
    verify_deployment_package_hash,
)
from apps.form_builder.models import FormDefinition, FormRevision, FormRevisionStatus
from apps.modules.models import ModuleRegistration
from apps.tenants.models import Tenant
from apps.themes.models import Theme, ThemeRevision, ThemeRevisionStatus


ROOT = Path(__file__).resolve().parents[3]
VALID_PACKAGE = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "deployment-package-field-ops.json"
VALID_APP = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "app-field-ops.json"
VALID_FORM = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "form-patient-intake.json"
VALID_MANIFEST = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "module-manifest-core.json"
VALID_THEME = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "theme-basic.json"


def load_valid_package() -> dict:
    with VALID_PACKAGE.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class DeploymentChannelModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="tenant_demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="tenant_other", name="Other Tenant")

    def test_default_release_channels_can_be_created_for_tenant(self):
        channels = create_default_release_channels(self.tenant)

        self.assertEqual([channel.channel for channel in channels], list(release_channel_names()))
        self.assertEqual(DeploymentChannel.objects.filter(tenant=self.tenant).count(), 4)

        second_call = create_default_release_channels(self.tenant)

        self.assertEqual([channel.id for channel in second_call], [channel.id for channel in channels])
        self.assertEqual(DeploymentChannel.objects.filter(tenant=self.tenant).count(), 4)

    def test_release_channel_is_unique_per_tenant(self):
        DeploymentChannel.objects.create(tenant=self.tenant, channel="dev", display_name="Development")

        with self.assertRaises(ValidationError):
            DeploymentChannel.objects.create(tenant=self.tenant, channel="dev", display_name="Development")

        other_channel = DeploymentChannel.objects.create(
            tenant=self.other_tenant,
            channel="dev",
            display_name="Development",
        )

        self.assertEqual(str(other_channel), "tenant_other:dev")

    def test_unknown_release_channel_is_rejected(self):
        channel = DeploymentChannel(tenant=self.tenant, channel="pilot", display_name="Pilot")

        with self.assertRaises(ValidationError):
            channel.full_clean()


class DeploymentPackageModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="tenant_demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="tenant_other", name="Other Tenant")
        self.payload = load_valid_package()

    def test_package_can_be_created_from_valid_payload(self):
        package = DeploymentPackage.from_payload(self.tenant, deepcopy(self.payload))
        package.save()

        self.assertEqual(package.package_id, "pkg_field_ops_001")
        self.assertEqual(package.app_id, "field_ops_app")
        self.assertEqual(package.app_version, "0.1.0")
        self.assertEqual(package.channel, "dev")
        self.assertEqual(package.status, DeploymentPackageStatus.SIGNED)
        self.assertEqual(str(package), "tenant_demo:pkg_field_ops_001")

    def test_invalid_package_payload_is_rejected(self):
        payload = deepcopy(self.payload)
        payload.pop("signature")
        package = DeploymentPackage.from_payload(self.tenant, deepcopy(self.payload))
        package.payload = payload

        with self.assertRaises(ValidationError):
            package.save()

    def test_model_metadata_must_match_payload(self):
        package = DeploymentPackage.from_payload(self.tenant, deepcopy(self.payload))
        package.app_version = "0.2.0"

        with self.assertRaises(ValidationError):
            package.full_clean()

    def test_package_id_is_unique_per_tenant(self):
        DeploymentPackage.from_payload(self.tenant, deepcopy(self.payload)).save()

        with self.assertRaises(ValidationError):
            DeploymentPackage.from_payload(self.tenant, deepcopy(self.payload)).save()

        other_payload = deepcopy(self.payload)
        other_payload["tenant_id"] = "tenant_other"
        other_payload["hash"] = package_hash(other_payload)
        other_package = DeploymentPackage.from_payload(self.other_tenant, other_payload)
        other_package.save()

        self.assertEqual(other_package.package_id, "pkg_field_ops_001")

    def test_tampered_package_payload_hash_is_rejected(self):
        payload = deepcopy(self.payload)
        payload["app"]["name"] = "Tampered Field Operations"
        package = DeploymentPackage.from_payload(self.tenant, payload)

        with self.assertRaises(ValidationError):
            package.save()

    def test_package_hash_metadata_must_match_payload_hash(self):
        payload = deepcopy(self.payload)
        payload["hash"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        package = DeploymentPackage.from_payload(self.tenant, payload)

        with self.assertRaises(ValidationError):
            package.save()

    def test_unknown_package_channel_is_rejected(self):
        payload = deepcopy(self.payload)
        payload["channel"] = "pilot"
        payload["hash"] = package_hash(payload)

        with self.assertRaises(ValidationError):
            DeploymentPackage.from_payload(self.tenant, payload).save()


class DeploymentPackageActivationTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="tenant_demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="tenant_other", name="Other Tenant")
        self.payload = load_valid_package()

    def package_payload(
        self,
        *,
        package_id: str,
        app_version: str,
        channel: str = "dev",
        tenant_slug: str = "tenant_demo",
    ):
        payload = deepcopy(self.payload)
        payload["package_id"] = package_id
        payload["tenant_id"] = tenant_slug
        payload["app_version"] = app_version
        payload["channel"] = channel
        payload["hash"] = package_hash(payload)
        return payload

    def save_package(self, *, package_id: str, app_version: str, channel: str = "dev", tenant=None):
        tenant = tenant or self.tenant
        payload = self.package_payload(
            package_id=package_id,
            app_version=app_version,
            channel=channel,
            tenant_slug=tenant.slug,
        )
        package = DeploymentPackage.from_payload(tenant, payload)
        package.save()
        return package

    def test_signed_package_can_be_activated_without_mutating_payload(self):
        package = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        original_payload = deepcopy(package.payload)

        activated = activate_deployment_package(package)

        self.assertEqual(activated.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(activated.payload, original_payload)
        self.assertEqual(
            active_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="dev"),
            activated,
        )

    def test_activation_archives_previous_active_package_for_same_tenant_app_channel(self):
        first = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        second = self.save_package(package_id="pkg_field_ops_003", app_version="0.3.0")

        activate_deployment_package(first)
        activated_second = activate_deployment_package(second)
        first.refresh_from_db()

        self.assertEqual(first.status, DeploymentPackageStatus.ARCHIVED)
        self.assertEqual(activated_second.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(
            active_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="dev"),
            activated_second,
        )

    def test_activation_is_scoped_by_channel_and_tenant(self):
        dev_package = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        staging_package = self.save_package(
            package_id="pkg_field_ops_003",
            app_version="0.2.0",
            channel="staging",
        )
        other_tenant_package = self.save_package(
            package_id="pkg_field_ops_002",
            app_version="0.2.0",
            tenant=self.other_tenant,
        )

        activate_deployment_package(dev_package)
        activate_deployment_package(staging_package)
        activate_deployment_package(other_tenant_package)
        dev_package.refresh_from_db()

        self.assertEqual(dev_package.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(
            active_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="staging"),
            staging_package,
        )
        self.assertEqual(
            active_deployment_package(tenant=self.other_tenant, app_id="field_ops_app", channel="dev"),
            other_tenant_package,
        )

    def test_activation_is_idempotent_for_current_active_package(self):
        package = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")

        first = activate_deployment_package(package)
        second = activate_deployment_package(first)

        self.assertEqual(second.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(
            DeploymentPackage.objects.filter(
                tenant=self.tenant,
                app_id="field_ops_app",
                channel="dev",
                status=DeploymentPackageStatus.ACTIVE,
            ).count(),
            1,
        )

    def test_archived_package_cannot_be_activated(self):
        package = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        package.status = DeploymentPackageStatus.ARCHIVED
        package.save()

        with self.assertRaises(ValidationError):
            activate_deployment_package(package)

    def test_rollback_reactivates_previous_archived_package(self):
        first = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        second = self.save_package(package_id="pkg_field_ops_003", app_version="0.3.0")
        first_payload = deepcopy(first.payload)

        activate_deployment_package(first)
        activate_deployment_package(second)
        rolled_back = rollback_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="dev")
        second.refresh_from_db()

        self.assertEqual(rolled_back.pk, first.pk)
        self.assertEqual(rolled_back.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(rolled_back.payload, first_payload)
        self.assertEqual(second.status, DeploymentPackageStatus.ARCHIVED)

    def test_rollback_can_target_specific_archived_package(self):
        first = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        second = self.save_package(package_id="pkg_field_ops_003", app_version="0.3.0")
        third = self.save_package(package_id="pkg_field_ops_004", app_version="0.4.0")

        activate_deployment_package(first)
        activate_deployment_package(second)
        activate_deployment_package(third)
        rolled_back = rollback_deployment_package(
            tenant=self.tenant,
            app_id="field_ops_app",
            channel="dev",
            package_id=first.package_id,
        )
        second.refresh_from_db()
        third.refresh_from_db()

        self.assertEqual(rolled_back.pk, first.pk)
        self.assertEqual(rolled_back.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(second.status, DeploymentPackageStatus.ARCHIVED)
        self.assertEqual(third.status, DeploymentPackageStatus.ARCHIVED)

    def test_rollback_is_scoped_by_channel(self):
        dev_first = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        dev_second = self.save_package(package_id="pkg_field_ops_003", app_version="0.3.0")
        staging_first = self.save_package(
            package_id="pkg_field_ops_004",
            app_version="0.2.0",
            channel="staging",
        )
        staging_second = self.save_package(
            package_id="pkg_field_ops_005",
            app_version="0.3.0",
            channel="staging",
        )

        activate_deployment_package(dev_first)
        activate_deployment_package(dev_second)
        activate_deployment_package(staging_first)
        activate_deployment_package(staging_second)
        rollback_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="staging")
        dev_second.refresh_from_db()
        staging_first.refresh_from_db()

        self.assertEqual(dev_second.status, DeploymentPackageStatus.ACTIVE)
        self.assertEqual(staging_first.status, DeploymentPackageStatus.ACTIVE)

    def test_rollback_rejects_missing_active_package(self):
        self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")

        with self.assertRaises(ValidationError):
            rollback_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="dev")

    def test_rollback_rejects_missing_target_package(self):
        package = self.save_package(package_id="pkg_field_ops_002", app_version="0.2.0")
        activate_deployment_package(package)

        with self.assertRaises(ValidationError):
            rollback_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="dev")

    def test_rollback_rejects_unknown_channel(self):
        with self.assertRaises(ValidationError):
            rollback_deployment_package(tenant=self.tenant, app_id="field_ops_app", channel="pilot")


class MobilePackageManifestEndpointTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="tenant_demo", name="Demo Tenant")
        self.payload = load_valid_package()

    def package_payload(self, *, package_id: str, app_version: str, channel: str = "dev"):
        payload = deepcopy(self.payload)
        payload["package_id"] = package_id
        payload["app_version"] = app_version
        payload["channel"] = channel
        payload["hash"] = package_hash(payload)
        return payload

    def save_active_package(
        self,
        *,
        package_id: str = "pkg_field_ops_002",
        app_version: str = "0.2.0",
        channel: str = "dev",
    ):
        package = DeploymentPackage.from_payload(
            self.tenant,
            self.package_payload(package_id=package_id, app_version=app_version, channel=channel),
        )
        package.save()
        return activate_deployment_package(package)

    def test_active_manifest_endpoint_returns_package_metadata(self):
        package = self.save_active_package()

        response = self.client.get(
            "/api/mobile/packages/manifest/",
            {"tenant": "tenant_demo", "app_id": "field_ops_app", "channel": "dev"},
        )

        self.assertEqual(response.status_code, 200)
        manifest = response.json()["manifest"]
        self.assertEqual(manifest["package_id"], package.package_id)
        self.assertEqual(manifest["app_id"], "field_ops_app")
        self.assertEqual(manifest["app_version"], "0.2.0")
        self.assertEqual(manifest["channel"], "dev")
        self.assertEqual(manifest["hash"], package.package_hash)
        self.assertEqual(manifest["signature"], package.signature)
        self.assertNotIn("payload", manifest)

    def test_active_manifest_endpoint_defaults_to_dev_channel(self):
        package = self.save_active_package()

        response = self.client.get(
            "/api/mobile/packages/manifest/",
            {"tenant": "tenant_demo", "app_id": "field_ops_app"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["manifest"]["package_id"], package.package_id)

    def test_active_manifest_endpoint_returns_not_found_without_active_package(self):
        response = self.client.get(
            "/api/mobile/packages/manifest/",
            {"tenant": "tenant_demo", "app_id": "field_ops_app"},
        )

        self.assertEqual(response.status_code, 404)

    def test_active_manifest_endpoint_requires_app_id(self):
        response = self.client.get("/api/mobile/packages/manifest/", {"tenant": "tenant_demo"})

        self.assertEqual(response.status_code, 400)

    def test_active_manifest_endpoint_rejects_unknown_channel(self):
        response = self.client.get(
            "/api/mobile/packages/manifest/",
            {"tenant": "tenant_demo", "app_id": "field_ops_app", "channel": "pilot"},
        )

        self.assertEqual(response.status_code, 400)

    def test_active_manifest_endpoint_rejects_post(self):
        response = self.client.post(
            "/api/mobile/packages/manifest/",
            {"tenant": "tenant_demo", "app_id": "field_ops_app"},
        )

        self.assertEqual(response.status_code, 405)

    def test_package_download_endpoint_returns_active_payload(self):
        package = self.save_active_package()

        response = self.client.get(
            f"/api/mobile/packages/{package.package_id}/download/",
            {"tenant": "tenant_demo"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["manifest"]["package_id"], package.package_id)
        self.assertEqual(body["manifest"]["hash"], package.package_hash)
        self.assertEqual(body["package"], package.payload)
        self.assertEqual(response.headers["ETag"], f'"{package.package_hash}"')

    def test_package_download_endpoint_rejects_inactive_package(self):
        payload = self.package_payload(package_id="pkg_field_ops_002", app_version="0.2.0")
        package = DeploymentPackage.from_payload(self.tenant, payload)
        package.save()

        response = self.client.get(
            f"/api/mobile/packages/{package.package_id}/download/",
            {"tenant": "tenant_demo"},
        )

        self.assertEqual(response.status_code, 409)

    def test_package_download_endpoint_returns_not_found_for_missing_package(self):
        response = self.client.get(
            "/api/mobile/packages/missing_package/download/",
            {"tenant": "tenant_demo"},
        )

        self.assertEqual(response.status_code, 404)

    def test_package_download_endpoint_requires_tenant(self):
        response = self.client.get("/api/mobile/packages/pkg_field_ops_002/download/")

        self.assertEqual(response.status_code, 400)

    def test_package_download_endpoint_rejects_post(self):
        response = self.client.post(
            "/api/mobile/packages/pkg_field_ops_002/download/",
            {"tenant": "tenant_demo"},
        )

        self.assertEqual(response.status_code, 405)


class DeploymentPackageCompilerTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="tenant_demo", name="Demo Tenant")
        self.module = ModuleRegistration.from_manifest(load_json(VALID_MANIFEST))
        self.module.save()

        self.theme_payload = load_json(VALID_THEME)
        self.theme = Theme.from_payload(self.tenant, self.theme_payload)
        self.theme.save()
        self.theme_revision = ThemeRevision.create_next(
            self.theme,
            deepcopy(self.theme_payload),
            status=ThemeRevisionStatus.PUBLISHED,
        )

        self.form_payload = load_json(VALID_FORM)
        self.form = FormDefinition.from_payload(self.tenant, self.form_payload)
        self.form.save()
        self.form_revision = FormRevision.create_next(
            self.form,
            deepcopy(self.form_payload),
            status=FormRevisionStatus.PUBLISHED,
        )

        self.app_payload = load_json(VALID_APP)
        self.app = AppDefinition.from_payload(self.tenant, self.app_payload)
        self.app.save()
        self.app_revision = AppRevision.create_next(
            self.app,
            deepcopy(self.app_payload),
            status=AppRevisionStatus.PUBLISHED,
        )

    def test_compiler_builds_contract_valid_payload(self):
        payload = compile_deployment_package_payload(
            tenant=self.tenant,
            package_id="pkg_field_ops_002",
            app_revision=self.app_revision,
            theme_revision=self.theme_revision,
            form_revisions=[self.form_revision],
            module_registrations=[self.module],
            runtime_min_version="0.1.0",
            runtime_max_version="0.1.0",
            created_by="builder",
        )

        self.assertEqual(payload["package_id"], "pkg_field_ops_002")
        self.assertEqual(payload["tenant_id"], "tenant_demo")
        self.assertEqual(payload["app_id"], "field_ops_app")
        self.assertEqual(payload["app"], self.app_payload)
        self.assertEqual(payload["theme"], self.theme_payload)
        self.assertEqual(payload["forms"], [self.form_payload])
        self.assertEqual(payload["modules"], [self.module.manifest])
        self.assertEqual(payload["created_by"], "builder")
        self.assertTrue(verify_deployment_package_hash(payload).is_valid)

    def test_compiler_uses_requested_release_channel(self):
        payload = compile_deployment_package_payload(
            tenant=self.tenant,
            package_id="pkg_field_ops_008",
            app_revision=self.app_revision,
            theme_revision=self.theme_revision,
            form_revisions=[self.form_revision],
            module_registrations=[self.module],
            runtime_min_version="0.1.0",
            runtime_max_version="0.1.0",
            channel="staging",
            created_by="builder",
        )

        self.assertEqual(payload["channel"], "staging")
        self.assertTrue(verify_deployment_package_hash(payload).is_valid)

    def test_compiler_can_persist_package(self):
        package = compile_deployment_package(
            tenant=self.tenant,
            package_id="pkg_field_ops_003",
            app_revision=self.app_revision,
            theme_revision=self.theme_revision,
            form_revisions=[self.form_revision],
            module_registrations=[self.module],
            runtime_min_version="0.1.0",
            runtime_max_version="0.1.0",
            created_by="builder",
        )

        self.assertEqual(package.package_id, "pkg_field_ops_003")
        self.assertEqual(package.status, DeploymentPackageStatus.SIGNED)
        self.assertTrue(package.package_hash.startswith("sha256:"))
        self.assertEqual(package.payload["forms"][0]["form_id"], "patient_intake")

    def test_signing_is_deterministic(self):
        payload = compile_deployment_package_payload(
            tenant=self.tenant,
            package_id="pkg_field_ops_004",
            app_revision=self.app_revision,
            theme_revision=self.theme_revision,
            form_revisions=[self.form_revision],
            module_registrations=[self.module],
            runtime_min_version="0.1.0",
            runtime_max_version="0.1.0",
            created_by="builder",
        )

        first = sign_deployment_package_payload(payload, "test-signing-key")
        second = sign_deployment_package_payload(payload, "test-signing-key")
        other_key = sign_deployment_package_payload(payload, "other-signing-key")

        self.assertEqual(first["hash"], second["hash"])
        self.assertEqual(first["signature"], second["signature"])
        self.assertTrue(first["hash"].startswith("sha256:"))
        self.assertTrue(first["signature"].startswith("hmac-sha256:"))
        self.assertNotEqual(first["signature"], other_key["signature"])
        self.assertTrue(verify_deployment_package_hash(first).is_valid)

    def test_hash_verification_detects_tampered_signed_payload(self):
        payload = compile_deployment_package_payload(
            tenant=self.tenant,
            package_id="pkg_field_ops_006",
            app_revision=self.app_revision,
            theme_revision=self.theme_revision,
            form_revisions=[self.form_revision],
            module_registrations=[self.module],
            runtime_min_version="0.1.0",
            runtime_max_version="0.1.0",
            created_by="builder",
            signing_key="test-signing-key",
        )
        tampered = deepcopy(payload)
        tampered["app"]["name"] = "Tampered Field Operations"

        verification = verify_deployment_package_hash(tampered)

        self.assertFalse(verification.is_valid)
        self.assertEqual(verification.actual_hash, payload["hash"])
        self.assertNotEqual(verification.expected_hash, payload["hash"])

    def test_compiler_rejects_hash_override_that_does_not_match_payload(self):
        with self.assertRaises(ValidationError):
            compile_deployment_package_payload(
                tenant=self.tenant,
                package_id="pkg_field_ops_007",
                app_revision=self.app_revision,
                theme_revision=self.theme_revision,
                form_revisions=[self.form_revision],
                module_registrations=[self.module],
                runtime_min_version="0.1.0",
                runtime_max_version="0.1.0",
                created_by="builder",
                package_hash="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )

    def test_compiler_can_persist_signed_package(self):
        package = compile_deployment_package(
            tenant=self.tenant,
            package_id="pkg_field_ops_005",
            app_revision=self.app_revision,
            theme_revision=self.theme_revision,
            form_revisions=[self.form_revision],
            module_registrations=[self.module],
            runtime_min_version="0.1.0",
            runtime_max_version="0.1.0",
            created_by="builder",
            signing_key="test-signing-key",
        )

        self.assertTrue(package.package_hash.startswith("sha256:"))
        self.assertTrue(package.signature.startswith("hmac-sha256:"))
        self.assertEqual(package.payload["hash"], package.package_hash)
        self.assertEqual(package.payload["signature"], package.signature)
