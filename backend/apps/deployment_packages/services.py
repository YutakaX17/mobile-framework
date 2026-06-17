from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.configurations.services import validate_configuration_payload


PLACEHOLDER_PACKAGE_HASH = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
PLACEHOLDER_PACKAGE_SIGNATURE = "compiler-placeholder-signature-v1-000"
RELEASE_CHANNELS = (
    ("dev", "Development"),
    ("test", "Test"),
    ("staging", "Staging"),
    ("production", "Production"),
)


def release_channel_choices() -> tuple[tuple[str, str], ...]:
    return RELEASE_CHANNELS


def release_channel_names() -> tuple[str, ...]:
    return tuple(channel for channel, _label in RELEASE_CHANNELS)


def validate_release_channel_name(channel: str) -> None:
    if channel not in release_channel_names():
        raise ValidationError({"channel": f"Unsupported release channel `{channel}`."})


def create_default_release_channels(tenant):
    from .models import DeploymentChannel

    channels = []
    for channel, label in RELEASE_CHANNELS:
        deployment_channel, _created = DeploymentChannel.objects.get_or_create(
            tenant=tenant,
            channel=channel,
            defaults={"display_name": label},
        )
        channels.append(deployment_channel)
    return channels


def activate_deployment_package(package):
    from .models import DeploymentPackage, DeploymentPackageStatus

    if not package.pk:
        raise ValidationError({"package": "Package must be saved before activation."})

    with transaction.atomic():
        package = DeploymentPackage.objects.select_for_update().get(pk=package.pk)
        if package.status == DeploymentPackageStatus.ARCHIVED:
            raise ValidationError({"status": "Archived packages cannot be activated."})

        was_already_active = package.status == DeploymentPackageStatus.ACTIVE
        DeploymentPackage.objects.select_for_update().filter(
            tenant=package.tenant,
            app_id=package.app_id,
            channel=package.channel,
            status=DeploymentPackageStatus.ACTIVE,
        ).exclude(pk=package.pk).update(status=DeploymentPackageStatus.ARCHIVED)

        if package.status != DeploymentPackageStatus.ACTIVE:
            package.status = DeploymentPackageStatus.ACTIVE
            package.save(update_fields=["status", "updated_at"])
        if not was_already_active:
            record_deployment_package_audit(
                package,
                action="deployment-package-activated",
            )
        return package


def active_deployment_package(*, tenant, app_id: str, channel: str = "dev"):
    from .models import DeploymentPackage, DeploymentPackageStatus

    validate_release_channel_name(channel)
    return (
        DeploymentPackage.objects.filter(
            tenant=tenant,
            app_id=app_id,
            channel=channel,
            status=DeploymentPackageStatus.ACTIVE,
        )
        .order_by("-updated_at", "-id")
        .first()
    )


def rollback_deployment_package(
    *,
    tenant,
    app_id: str,
    channel: str = "dev",
    package_id: str | None = None,
):
    from .models import DeploymentPackage, DeploymentPackageStatus

    validate_release_channel_name(channel)
    with transaction.atomic():
        packages = DeploymentPackage.objects.select_for_update().filter(
            tenant=tenant,
            app_id=app_id,
            channel=channel,
        )
        current = packages.filter(status=DeploymentPackageStatus.ACTIVE).order_by(
            "-updated_at",
            "-id",
        ).first()
        if current is None:
            raise ValidationError({"status": "Rollback requires an active package."})

        candidates = packages.filter(status=DeploymentPackageStatus.ARCHIVED)
        if package_id:
            target = candidates.filter(package_id=package_id).first()
        else:
            target = candidates.order_by("-updated_at", "-id").first()
        if target is None:
            raise ValidationError({"package": "Rollback target package was not found."})

        current.status = DeploymentPackageStatus.ARCHIVED
        current.save(update_fields=["status", "updated_at"])
        target.status = DeploymentPackageStatus.ACTIVE
        target.save(update_fields=["status", "updated_at"])
        record_deployment_package_audit(
            target,
            action="deployment-package-rolled-back",
            metadata={"previous_active_package_id": current.package_id},
        )
        return target


def record_deployment_package_audit(
    package,
    *,
    action: str,
    actor=None,
    metadata: dict[str, Any] | None = None,
):
    from apps.audit.models import AuditEvent, AuditEventType, AuditSeverity

    event_metadata = {
        "app_id": package.app_id,
        "app_version": package.app_version,
        "channel": package.channel,
        "package_hash": package.package_hash,
        "runtime_max_version": package.runtime_max_version,
        "runtime_min_version": package.runtime_min_version,
    }
    if metadata:
        event_metadata.update(metadata)
    return AuditEvent.objects.create(
        tenant=package.tenant,
        actor=actor,
        event_type=AuditEventType.DEPLOYMENT,
        severity=AuditSeverity.INFO,
        action=action,
        target_type="deployment_package",
        target_id=package.package_id,
        target_repr=str(package),
        metadata=event_metadata,
    )


@dataclass(frozen=True)
class PackageHashVerification:
    is_valid: bool
    expected_hash: str
    actual_hash: str | None


def validate_deployment_package_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("deployment_package", payload)


def canonical_unsigned_package_json(payload: dict[str, Any]) -> str:
    unsigned_payload = {key: value for key, value in payload.items() if key not in {"hash", "signature"}}
    return json.dumps(unsigned_payload, separators=(",", ":"), sort_keys=True)


def calculate_package_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_unsigned_package_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def package_hash(payload: dict[str, Any]) -> str:
    return calculate_package_hash(payload)


def verify_deployment_package_hash(payload: dict[str, Any]) -> PackageHashVerification:
    actual_hash = payload.get("hash")
    expected_hash = calculate_package_hash(payload)
    is_valid = isinstance(actual_hash, str) and hmac.compare_digest(actual_hash, expected_hash)
    return PackageHashVerification(
        is_valid=is_valid,
        expected_hash=expected_hash,
        actual_hash=actual_hash if isinstance(actual_hash, str) else None,
    )


def assert_deployment_package_hash(payload: dict[str, Any]) -> None:
    verification = verify_deployment_package_hash(payload)
    if not verification.is_valid:
        raise ValidationError(
            {
                "hash": (
                    "Must match canonical unsigned package payload hash "
                    f"`{verification.expected_hash}`."
                )
            }
        )


def package_signature(package_hash_value: str, signing_key: str) -> str:
    digest = hmac.new(signing_key.encode("utf-8"), package_hash_value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


def sign_deployment_package_payload(payload: dict[str, Any], signing_key: str) -> dict[str, Any]:
    signed_payload = dict(payload)
    signed_payload["hash"] = calculate_package_hash(signed_payload)
    signed_payload["signature"] = package_signature(signed_payload["hash"], signing_key)
    validate_deployment_package_payload(signed_payload)
    assert_deployment_package_hash(signed_payload)
    return signed_payload


def compile_deployment_package_payload(
    *,
    tenant,
    package_id: str,
    app_revision,
    theme_revision,
    form_revisions,
    module_registrations,
    runtime_min_version: str,
    runtime_max_version: str,
    channel: str = "dev",
    platform_version: str = "0.1.0",
    created_by: str = "system",
    package_hash: str | None = None,
    signature: str = PLACEHOLDER_PACKAGE_SIGNATURE,
    signing_key: str | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "v1",
        "package_id": package_id,
        "tenant_id": tenant.slug,
        "app_id": app_revision.payload["app_id"],
        "app_version": app_revision.version,
        "runtime_min_version": runtime_min_version,
        "runtime_max_version": runtime_max_version,
        "platform_version": platform_version,
        "channel": channel,
        "modules": [registration.manifest for registration in module_registrations],
        "theme": theme_revision.payload,
        "app": app_revision.payload,
        "forms": [revision.payload for revision in form_revisions],
        "assets": [],
        "sync_rules": [],
        "created_at": timezone.now().isoformat(),
        "created_by": created_by,
        "hash": package_hash or PLACEHOLDER_PACKAGE_HASH,
        "signature": signature,
    }
    if signing_key:
        payload = sign_deployment_package_payload(payload, signing_key)
    elif package_hash is None:
        payload["hash"] = calculate_package_hash(payload)
    validate_deployment_package_payload(payload)
    assert_deployment_package_hash(payload)
    return payload


def compile_deployment_package(**kwargs):
    from .models import DeploymentPackage

    payload = compile_deployment_package_payload(**kwargs)
    package = DeploymentPackage.from_payload(kwargs["tenant"], payload)
    package.save()
    return package
