import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.tenants.models import Tenant
from apps.themes.models import Theme, ThemeRevision, ThemeRevisionStatus


ROOT = Path(__file__).resolve().parents[3]
VALID_THEME = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "theme-basic.json"


def load_valid_theme() -> dict:
    with VALID_THEME.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class ThemeRegistryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.payload = load_valid_theme()
        self.theme = Theme.from_payload(self.tenant, self.payload)
        self.theme.save()

    def test_theme_can_be_created_from_valid_payload(self):
        self.assertEqual(self.theme.theme_id, "field_ops")
        self.assertEqual(self.theme.name, "Field Operations")
        self.assertEqual(self.theme.description, "Accessible starter theme for mobile field work.")
        self.assertEqual(str(self.theme), "demo:field_ops")

    def test_valid_theme_revision_is_created(self):
        revision = ThemeRevision.create_next(
            self.theme,
            deepcopy(self.payload),
            status=ThemeRevisionStatus.VALIDATED,
        )

        self.assertEqual(revision.revision, 1)
        self.assertEqual(revision.version, "0.1.0")
        self.assertEqual(revision.schema_version, "v1")
        self.assertEqual(revision.status, ThemeRevisionStatus.VALIDATED)
        self.assertEqual(str(revision), "demo:field_ops#1")

    def test_invalid_theme_payload_is_rejected(self):
        payload = deepcopy(self.payload)
        payload.pop("name")

        with self.assertRaises(ValidationError):
            ThemeRevision.create_next(self.theme, payload)

    def test_theme_id_is_unique_per_tenant(self):
        with self.assertRaises(ValidationError):
            Theme.from_payload(self.tenant, self.payload).save()

        other_tenant_theme = Theme.from_payload(self.other_tenant, self.payload)
        other_tenant_theme.save()

        self.assertEqual(other_tenant_theme.theme_id, "field_ops")

    def test_revision_numbering_increments_per_theme(self):
        first = ThemeRevision.create_next(self.theme, deepcopy(self.payload))
        second = ThemeRevision.create_next(self.theme, deepcopy(self.payload))

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)

    def test_revision_fields_must_match_payload(self):
        payload = deepcopy(self.payload)
        payload["theme_id"] = "other_theme"

        with self.assertRaises(ValidationError):
            ThemeRevision.create_next(self.theme, payload)

    def test_current_revision_must_belong_to_theme(self):
        revision = ThemeRevision.create_next(self.theme, deepcopy(self.payload))
        other_payload = deepcopy(self.payload)
        other_payload["theme_id"] = "other_theme"
        other_payload["name"] = "Other Theme"
        other_theme = Theme.from_payload(self.tenant, other_payload)
        other_theme.save()

        other_theme.current_revision = revision

        with self.assertRaises(ValidationError):
            other_theme.full_clean()

    def test_revision_tenant_must_match_theme_tenant(self):
        revision = ThemeRevision(
            tenant=self.other_tenant,
            theme=self.theme,
            revision=1,
            version=self.payload["version"],
            payload=deepcopy(self.payload),
        )

        with self.assertRaises(ValidationError):
            revision.full_clean()
