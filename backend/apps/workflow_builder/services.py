from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_SCHEMA = ROOT / "contracts" / "schemas" / "v1" / "workflow.schema.json"


@lru_cache(maxsize=1)
def workflow_schema() -> dict[str, Any]:
    with WORKFLOW_SCHEMA.open(encoding="utf-8-sig") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=1)
def workflow_validator() -> Draft202012Validator:
    return Draft202012Validator(workflow_schema())


def validate_workflow_payload(payload: dict[str, Any]) -> None:
    try:
        workflow_validator().validate(payload)
    except JsonSchemaValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = f" at {path}" if path else ""
        raise ValidationError({"payload": f"Invalid workflow definition{location}: {exc.message}"}) from exc

    validate_workflow_state_machine(payload)


def duplicate_values(values: list[str]) -> list[str]:
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def validate_unique_ids(label: str, values: list[str]) -> None:
    duplicates = duplicate_values(values)
    if duplicates:
        formatted = ", ".join(duplicates)
        raise ValidationError({"payload": f"Workflow {label} must be unique: {formatted}"})


def validate_workflow_state_machine(payload: dict[str, Any]) -> None:
    states = payload.get("states", [])
    transitions = payload.get("transitions", [])
    triggers = payload.get("triggers", [])

    state_ids = [state["state_id"] for state in states]
    trigger_ids = [trigger["trigger_id"] for trigger in triggers]
    transition_ids = [transition["transition_id"] for transition in transitions]

    validate_unique_ids("state IDs", state_ids)
    validate_unique_ids("trigger IDs", trigger_ids)
    validate_unique_ids("transition IDs", transition_ids)

    states_by_id = {state["state_id"]: state for state in states}
    trigger_id_set = set(trigger_ids)
    initial_state = payload["initial_state"]

    if initial_state not in states_by_id:
        raise ValidationError({"initial_state": "Must reference a defined workflow state."})

    if states_by_id[initial_state]["state_type"] != "start":
        raise ValidationError({"initial_state": "Must reference a start state."})

    start_states = sorted(
        state["state_id"] for state in states if state["state_type"] == "start"
    )
    if start_states != [initial_state]:
        formatted = ", ".join(start_states)
        raise ValidationError({"states": f"Workflow must define exactly one start state: {formatted}"})

    outgoing: dict[str, set[str]] = {state_id: set() for state_id in state_ids}
    for transition in transitions:
        from_state = transition["from_state"]
        to_state = transition["to_state"]
        trigger = transition["trigger"]

        if from_state not in states_by_id:
            raise ValidationError(
                {"transitions": f"Transition `{transition['transition_id']}` has unknown from_state."}
            )
        if to_state not in states_by_id:
            raise ValidationError(
                {"transitions": f"Transition `{transition['transition_id']}` has unknown to_state."}
            )
        if trigger not in trigger_id_set:
            raise ValidationError(
                {"transitions": f"Transition `{transition['transition_id']}` has unknown trigger."}
            )

        outgoing[from_state].add(to_state)

    reachable = {initial_state}
    pending = [initial_state]
    while pending:
        state_id = pending.pop()
        for next_state in outgoing[state_id]:
            if next_state not in reachable:
                reachable.add(next_state)
                pending.append(next_state)

    unreachable = sorted(set(state_ids) - reachable)
    if unreachable:
        formatted = ", ".join(unreachable)
        raise ValidationError(
            {"states": f"Workflow states must be reachable from the initial state: {formatted}"}
        )
