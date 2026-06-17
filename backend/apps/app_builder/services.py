from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.configurations.services import validate_configuration_payload


def validate_app_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("app", payload)


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
