import json
from copy import deepcopy
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.configurations.models import (
    ConfigurationDefinition,
    ConfigurationKind,
    ConfigurationRevision,
    ConfigurationRevisionStatus,
)
from apps.tenants.models import Tenant


ROOT = Path(__file__).resolve().parents[3]
VALID_THEME = ROOT / "contracts" / "fixtures" / "valid" / "v1" / "theme-basic.json"


def load_valid_theme() -> dict:
    with VALID_THEME.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


class ConfigurationRegistryTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(slug="demo", name="Demo Tenant")
        self.other_tenant = Tenant.objects.create(slug="other", name="Other Tenant")
        self.definition = ConfigurationDefinition.objects.create(
            tenant=self.tenant,
            kind=ConfigurationKind.THEME,
            key="field-ops",
            name="Field Operations",
        )

    def test_valid_configuration_revision_is_created(self):
        revision = ConfigurationRevision.create_next(
            self.definition,
            load_valid_theme(),
            status=ConfigurationRevisionStatus.VALIDATED,
        )

        self.assertEqual(revision.revision, 1)
        self.assertEqual(revision.status, ConfigurationRevisionStatus.VALIDATED)
        self.assertEqual(str(revision), "demo:theme:field-ops#1")

    def test_invalid_payload_is_rejected(self):
        payload = load_valid_theme()
        payload.pop("name")

        with self.assertRaises(ValidationError):
            ConfigurationRevision.create_next(self.definition, payload)

    def test_definition_key_is_unique_per_tenant_and_kind(self):
        with self.assertRaises(ValidationError):
            ConfigurationDefinition.objects.create(
                tenant=self.tenant,
                kind=ConfigurationKind.THEME,
                key="field-ops",
                name="Duplicate",
            )

        field_definition = ConfigurationDefinition.objects.create(
            tenant=self.tenant,
            kind=ConfigurationKind.FIELD,
            key="field-ops",
            name="Field",
        )
        other_tenant_definition = ConfigurationDefinition.objects.create(
            tenant=self.other_tenant,
            kind=ConfigurationKind.THEME,
            key="field-ops",
            name="Other Tenant Theme",
        )

        self.assertEqual(field_definition.key, "field-ops")
        self.assertEqual(other_tenant_definition.key, "field-ops")

    def test_revision_numbering_increments_per_definition(self):
        payload = load_valid_theme()

        first = ConfigurationRevision.create_next(self.definition, deepcopy(payload))
        second = ConfigurationRevision.create_next(self.definition, deepcopy(payload))

        self.assertEqual(first.revision, 1)
        self.assertEqual(second.revision, 2)

    def test_current_revision_must_belong_to_definition(self):
        revision = ConfigurationRevision.create_next(self.definition, load_valid_theme())
        other_definition = ConfigurationDefinition.objects.create(
            tenant=self.tenant,
            kind=ConfigurationKind.THEME,
            key="other-theme",
            name="Other Theme",
        )

        other_definition.current_revision = revision

        with self.assertRaises(ValidationError):
            other_definition.full_clean()

    def test_revision_tenant_must_match_definition_tenant(self):
        revision = ConfigurationRevision(
            tenant=self.other_tenant,
            definition=self.definition,
            revision=1,
            payload=load_valid_theme(),
        )

        with self.assertRaises(ValidationError):
            revision.full_clean()
