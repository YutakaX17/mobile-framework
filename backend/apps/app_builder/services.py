from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.configurations.services import validate_configuration_payload


def validate_app_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("app", payload)


@transaction.atomic
def create_app_draft_revision(app, payload: dict[str, Any], created_by=None):
    from .models import AppRevision, AppRevisionStatus

    validate_app_payload(payload)
    if payload.get("app_id") != app.app_id:
        raise ValidationError({"app_id": f"Must match existing app id `{app.app_id}`."})

    app.name = payload["name"]
    app.description = payload.get("description", "")
    app.save(update_fields=["name", "description", "updated_at"])

    return AppRevision.create_next(
        app,
        payload,
        created_by=created_by,
        status=AppRevisionStatus.DRAFT,
    )


@transaction.atomic
def publish_app_revision(app, revision):
    from .models import AppRevision, AppRevisionStatus

    AppRevision.objects.filter(app=app, status=AppRevisionStatus.PUBLISHED).exclude(pk=revision.pk).update(
        status=AppRevisionStatus.ARCHIVED
    )

    revision.status = AppRevisionStatus.PUBLISHED
    revision.save(update_fields=["status", "updated_at"])

    app.current_revision = revision
    app.save(update_fields=["current_revision", "updated_at"])
    return revision
