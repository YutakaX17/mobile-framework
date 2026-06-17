import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.deployment_packages.models import DeploymentPackage, DeploymentPackageStatus
from apps.tenants.models import Tenant


ROOT = Path(__file__).resolve().parents[3]
VALID_PACKAGE = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "deployment-package-field-ops.json"


def load_valid_package() -> dict:
    with VALID_PACKAGE.open(encoding="utf-8-sig") as handle:
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

        other_package = DeploymentPackage.from_payload(self.other_tenant, deepcopy(self.payload))
        other_package.payload["tenant_id"] = "tenant_other"
        other_package.save()

        self.assertEqual(other_package.package_id, "pkg_field_ops_001")
