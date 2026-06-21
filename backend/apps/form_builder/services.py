from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.configurations.services import validate_configuration_payload


def validate_form_payload(payload: dict[str, Any]) -> None:
    validate_configuration_payload("form", payload)


@transaction.atomic
def create_form_draft_revision(form, payload: dict[str, Any], created_by=None):
    from .models import FormRevision, FormRevisionStatus

    validate_form_payload(payload)
    if payload.get("form_id") != form.form_id:
        raise ValidationError({"form_id": f"Must match existing form id `{form.form_id}`."})

    form.name = payload["name"]
    form.description = payload.get("description", "")
    form.mode = payload["mode"]
    form.save(update_fields=["name", "description", "mode", "updated_at"])

    return FormRevision.create_next(
        form,
        payload,
        created_by=created_by,
        status=FormRevisionStatus.DRAFT,
    )


@transaction.atomic
def publish_form_revision(form, revision):
    from .models import FormRevision, FormRevisionStatus

    FormRevision.objects.filter(form=form, status=FormRevisionStatus.PUBLISHED).exclude(pk=revision.pk).update(
        status=FormRevisionStatus.ARCHIVED
    )

    revision.status = FormRevisionStatus.PUBLISHED
    revision.save(update_fields=["status", "updated_at"])

    form.current_revision = revision
    form.save(update_fields=["current_revision", "updated_at"])
    return revision
