import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.app_builder.models import AppDefinition, AppRevision, AppRevisionStatus
from apps.deployment_packages.models import DeploymentPackage, DeploymentPackageStatus
from apps.deployment_packages.services import (
    compile_deployment_package,
    compile_deployment_package_payload,
    package_hash,
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
