from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.configurations.services import validate_configuration_payload


def validate_theme_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("theme", payload)


@transaction.atomic
def publish_theme_revision(theme, revision):
    from .models import ThemeRevision, ThemeRevisionStatus

    ThemeRevision.objects.filter(theme=theme, status=ThemeRevisionStatus.PUBLISHED).exclude(pk=revision.pk).update(
        status=ThemeRevisionStatus.ARCHIVED
    )

    revision.status = ThemeRevisionStatus.PUBLISHED
    revision.save(update_fields=["status", "updated_at"])

    theme.current_revision = revision
    theme.save(update_fields=["current_revision", "updated_at"])
    return revision


def rollback_theme_revision(theme, revision):
    return publish_theme_revision(theme, revision)
