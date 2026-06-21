from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.app_builder.models import AppDefinition, AppRevision, AppRevisionStatus
from apps.app_builder.services import publish_app_revision
from apps.deployment_packages.models import DeploymentPackage, DeploymentPackageStatus
from apps.deployment_packages.services import (
    activate_deployment_package,
    compile_deployment_package,
    create_default_release_channels,
)
from apps.form_builder.models import FormDefinition, FormRevision, FormRevisionStatus
from apps.identity.models import PlatformPermission, PlatformRole, RolePermission, UserRoleAssignment
from apps.modules.models import ModuleRegistration, ModuleRegistrationStatus
from apps.tenants.models import Tenant, TenantStatus
from apps.themes.models import Theme, ThemeRevision, ThemeRevisionStatus
from apps.themes.services import publish_theme_revision


ROOT = Path(__file__).resolve().parents[5]
FIXTURES = ROOT / "contracts" / "fixtures" / "valid" / "v1"
DEFAULT_ADMIN_USERNAME = "demo-admin"
DEFAULT_ADMIN_EMAIL = "demo-admin@example.com"
DEFAULT_ADMIN_PASSWORD = "demo-admin-password"
DEFAULT_SIGNING_KEY = "local-demo-mvp-signing-key"
DEMO_PACKAGE_ID = "pkg_demo_field_ops_001"

PERMISSIONS = (
    ("core.view_dashboard", "View dashboard"),
    ("builder.theme.manage", "Manage themes"),
    ("builder.form.manage", "Manage forms"),
    ("builder.app.manage", "Manage apps"),
    ("builder.package.publish", "Publish deployment packages"),
    ("forms.submit_patient_intake", "Submit patient intake"),
    ("mobile.package.read", "Read active mobile packages"),
    ("sync.submit", "Submit mobile sync batches"),
)

ROLES = {
    "admin": {
        "name": "Administrator",
        "description": "Full demo tenant administration role.",
        "permissions": tuple(code for code, _name in PERMISSIONS),
    },
    "configurator": {
        "name": "Configurator",
        "description": "Can configure and publish the demo app.",
        "permissions": (
            "core.view_dashboard",
            "builder.theme.manage",
            "builder.form.manage",
            "builder.app.manage",
            "builder.package.publish",
        ),
    },
    "mobile-user": {
        "name": "Mobile User",
        "description": "Can use the demo mobile package and submit intake forms.",
        "permissions": (
            "forms.submit_patient_intake",
            "mobile.package.read",
            "sync.submit",
        ),
    },
}


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES / name).open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def payload_matches(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left == right


class Command(BaseCommand):
    help = "Seed an idempotent local end-to-end MVP demo tenant, admin user, builders, and active dev package."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-slug", default="demo")
        parser.add_argument("--tenant-name", default="Demo Tenant")
        parser.add_argument("--admin-username", default=DEFAULT_ADMIN_USERNAME)
        parser.add_argument("--admin-email", default=DEFAULT_ADMIN_EMAIL)
        parser.add_argument(
            "--admin-password",
            default=os.environ.get("DEMO_MVP_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
            help="Demo admin password. Defaults to DEMO_MVP_ADMIN_PASSWORD or a local-only documented password.",
        )
        parser.add_argument(
            "--signing-key",
            default=os.environ.get("DEMO_MVP_SIGNING_KEY", DEFAULT_SIGNING_KEY),
            help="Local HMAC signing key for the demo package.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant = self.seed_tenant(options["tenant_slug"], options["tenant_name"])
        admin = self.seed_admin_user(
            username=options["admin_username"],
            email=options["admin_email"],
            password=options["admin_password"],
        )
        permissions = self.seed_permissions()
        roles = self.seed_roles(tenant, permissions)
        self.seed_admin_assignment(tenant, admin, roles["admin"])
        channels = create_default_release_channels(tenant)
        module = self.seed_module(load_fixture("module-manifest-core.json"))
        theme_revision = self.seed_theme(tenant, load_fixture("theme-basic.json"), admin)
        form_revision = self.seed_form(tenant, load_fixture("form-patient-intake.json"), admin)
        app_revision = self.seed_app(tenant, load_fixture("app-field-ops.json"), admin)
        package = self.seed_package(
            tenant=tenant,
            admin=admin,
            app_revision=app_revision,
            theme_revision=theme_revision,
            form_revision=form_revision,
            module=module,
            signing_key=options["signing_key"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded demo MVP tenant "
                f"`{tenant.slug}` with admin `{admin.username}`, "
                f"{len(channels)} release channels, and active package `{package.package_id}`."
            )
        )

    def seed_tenant(self, slug: str, name: str) -> Tenant:
        tenant, _created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "status": TenantStatus.ACTIVE},
        )
        updates: list[str] = []
        if tenant.name != name:
            tenant.name = name
            updates.append("name")
        if tenant.status != TenantStatus.ACTIVE:
            tenant.status = TenantStatus.ACTIVE
            updates.append("status")
        if updates:
            tenant.save(update_fields=[*updates, "updated_at"])
        return tenant

    def seed_admin_user(self, *, username: str, email: str, password: str):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        updates: list[str] = []
        if user.email != email:
            user.email = email
            updates.append("email")
        if not user.is_staff:
            user.is_staff = True
            updates.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            updates.append("is_superuser")
        if created or not user.has_usable_password():
            user.set_password(password)
            updates.append("password")
        if updates:
            user.save(update_fields=updates)
        return user

    def seed_permissions(self) -> dict[str, PlatformPermission]:
        seeded = {}
        for code, name in PERMISSIONS:
            permission, _created = PlatformPermission.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )
            seeded[code] = permission
        return seeded

    def seed_roles(
        self,
        tenant: Tenant,
        permissions: dict[str, PlatformPermission],
    ) -> dict[str, PlatformRole]:
        seeded = {}
        for slug, role_spec in ROLES.items():
            role, _created = PlatformRole.objects.update_or_create(
                tenant=tenant,
                slug=slug,
                defaults={
                    "name": role_spec["name"],
                    "description": role_spec["description"],
                    "is_system": True,
                },
            )
            seeded[slug] = role
            for permission_code in role_spec["permissions"]:
                RolePermission.objects.get_or_create(role=role, permission=permissions[permission_code])
        return seeded

    def seed_admin_assignment(self, tenant: Tenant, admin, role: PlatformRole) -> None:
        assignment, _created = UserRoleAssignment.objects.get_or_create(
            tenant=tenant,
            user=admin,
            role=role,
            defaults={"is_active": True},
        )
        if not assignment.is_active:
            assignment.is_active = True
            assignment.save(update_fields=["is_active", "updated_at"])

    def seed_module(self, manifest: dict[str, Any]) -> ModuleRegistration:
        module, created = ModuleRegistration.objects.get_or_create(
            module_id=manifest["module_id"],
            version=manifest["version"],
            defaults={
                "name": manifest["name"],
                "schema_version": manifest["schema_version"],
                "plugin_api_version": manifest["plugin_api_version"],
                "platform_min_version": manifest["platform_min_version"],
                "platform_max_version": manifest.get("platform_max_version", ""),
                "manifest": manifest,
                "status": ModuleRegistrationStatus.ENABLED,
            },
        )
        if not created:
            module.name = manifest["name"]
            module.schema_version = manifest["schema_version"]
            module.plugin_api_version = manifest["plugin_api_version"]
            module.platform_min_version = manifest["platform_min_version"]
            module.platform_max_version = manifest.get("platform_max_version", "")
            module.manifest = manifest
            module.status = ModuleRegistrationStatus.ENABLED
            module.save()
        return module

    def seed_theme(self, tenant: Tenant, payload: dict[str, Any], admin) -> ThemeRevision:
        theme, created = Theme.objects.get_or_create(
            tenant=tenant,
            theme_id=payload["theme_id"],
            defaults={
                "name": payload["name"],
                "description": payload.get("description", ""),
            },
        )
        if not created and (theme.name != payload["name"] or theme.description != payload.get("description", "")):
            theme.name = payload["name"]
            theme.description = payload.get("description", "")
            theme.save(update_fields=["name", "description", "updated_at"])

        revision = self.matching_theme_revision(theme, payload)
        if revision is None:
            revision = ThemeRevision.create_next(
                theme,
                deepcopy(payload),
                created_by=admin,
                status=ThemeRevisionStatus.VALIDATED,
            )
        publish_theme_revision(theme, revision)
        return revision

    def matching_theme_revision(self, theme: Theme, payload: dict[str, Any]) -> ThemeRevision | None:
        for revision in theme.revisions.all():
            if payload_matches(revision.payload, payload):
                return revision
        return None

    def seed_form(self, tenant: Tenant, payload: dict[str, Any], admin) -> FormRevision:
        form, created = FormDefinition.objects.get_or_create(
            tenant=tenant,
            form_id=payload["form_id"],
            defaults={
                "name": payload["name"],
                "description": payload.get("description", ""),
                "mode": payload["mode"],
            },
        )
        form_updates: list[str] = []
        if not created:
            if form.name != payload["name"]:
                form.name = payload["name"]
                form_updates.append("name")
            if form.description != payload.get("description", ""):
                form.description = payload.get("description", "")
                form_updates.append("description")
            if form.mode != payload["mode"]:
                form.mode = payload["mode"]
                form_updates.append("mode")
        if form_updates:
            form.save(update_fields=[*form_updates, "updated_at"])

        revision = self.matching_form_revision(form, payload)
        if revision is None:
            revision = FormRevision.create_next(
                form,
                deepcopy(payload),
                created_by=admin,
                status=FormRevisionStatus.REVIEWED,
            )
        FormRevision.objects.filter(form=form, status=FormRevisionStatus.PUBLISHED).exclude(pk=revision.pk).update(
            status=FormRevisionStatus.ARCHIVED
        )
        if revision.status != FormRevisionStatus.PUBLISHED:
            revision.status = FormRevisionStatus.PUBLISHED
            revision.save(update_fields=["status", "updated_at"])
        if form.current_revision_id != revision.id:
            form.current_revision = revision
            form.save(update_fields=["current_revision", "updated_at"])
        return revision

    def matching_form_revision(self, form: FormDefinition, payload: dict[str, Any]) -> FormRevision | None:
        for revision in form.revisions.all():
            if payload_matches(revision.payload, payload):
                return revision
        return None

    def seed_app(self, tenant: Tenant, payload: dict[str, Any], admin) -> AppRevision:
        app, created = AppDefinition.objects.get_or_create(
            tenant=tenant,
            app_id=payload["app_id"],
            defaults={
                "name": payload["name"],
                "description": payload.get("description", ""),
            },
        )
        if not created and (app.name != payload["name"] or app.description != payload.get("description", "")):
            app.name = payload["name"]
            app.description = payload.get("description", "")
            app.save(update_fields=["name", "description", "updated_at"])

        revision = self.matching_app_revision(app, payload)
        if revision is None:
            revision = AppRevision.create_next(
                app,
                deepcopy(payload),
                created_by=admin,
                status=AppRevisionStatus.REVIEWED,
            )
        publish_app_revision(app, revision)
        return revision

    def matching_app_revision(self, app: AppDefinition, payload: dict[str, Any]) -> AppRevision | None:
        for revision in app.revisions.all():
            if payload_matches(revision.payload, payload):
                return revision
        return None

    def seed_package(
        self,
        *,
        tenant: Tenant,
        admin,
        app_revision: AppRevision,
        theme_revision: ThemeRevision,
        form_revision: FormRevision,
        module: ModuleRegistration,
        signing_key: str,
    ) -> DeploymentPackage:
        package = DeploymentPackage.objects.filter(tenant=tenant, package_id=DEMO_PACKAGE_ID).first()
        if package is None:
            package = compile_deployment_package(
                tenant=tenant,
                package_id=DEMO_PACKAGE_ID,
                app_revision=app_revision,
                theme_revision=theme_revision,
                form_revisions=[form_revision],
                module_registrations=[module],
                runtime_min_version="0.1.0",
                runtime_max_version="0.1.0",
                channel="dev",
                platform_version="0.1.0",
                created_by=admin.username,
                signing_key=signing_key,
            )

        if package.status == DeploymentPackageStatus.ARCHIVED:
            package.status = DeploymentPackageStatus.SIGNED
            package.save(update_fields=["status", "updated_at"])
        return activate_deployment_package(package)
