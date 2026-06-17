from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from django.utils import timezone

from apps.configurations.services import validate_configuration_payload


PLACEHOLDER_PACKAGE_HASH = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
PLACEHOLDER_PACKAGE_SIGNATURE = "compiler-placeholder-signature-v1-000"


def validate_deployment_package_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("deployment_package", payload)


def canonical_unsigned_package_json(payload: dict[str, Any]) -> str:
    unsigned_payload = {key: value for key, value in payload.items() if key not in {"hash", "signature"}}
    return json.dumps(unsigned_payload, separators=(",", ":"), sort_keys=True)


def package_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_unsigned_package_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def package_signature(package_hash_value: str, signing_key: str) -> str:
    digest = hmac.new(signing_key.encode("utf-8"), package_hash_value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


def sign_deployment_package_payload(payload: dict[str, Any], signing_key: str) -> dict[str, Any]:
    signed_payload = dict(payload)
    signed_payload["hash"] = package_hash(signed_payload)
    signed_payload["signature"] = package_signature(signed_payload["hash"], signing_key)
    validate_deployment_package_payload(signed_payload)
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
    package_hash: str = PLACEHOLDER_PACKAGE_HASH,
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
        "hash": package_hash,
        "signature": signature,
    }
    if signing_key:
        payload = sign_deployment_package_payload(payload, signing_key)
    validate_deployment_package_payload(payload)
    return payload


def compile_deployment_package(**kwargs):
    from .models import DeploymentPackage

    payload = compile_deployment_package_payload(**kwargs)
    package = DeploymentPackage.from_payload(kwargs["tenant"], payload)
    package.save()
    return package
