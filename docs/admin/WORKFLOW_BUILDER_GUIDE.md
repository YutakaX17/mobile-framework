# Workflow Builder Guide

This guide describes the current workflow builder baseline for administrators and builders. It focuses on the implemented editor surface, sample workflow payload, state-machine validation rules, task inbox baseline, and backend workflow models.

## Access

The Workflows module is available to users with `workflows:manage` or `platform-admin`.

Route:

- `/workflows`: workflow editor baseline.

If the route shows an unauthorized state, confirm the user has the `operator` role or another role that grants `workflows:manage`.

## Current Baseline

The workflow editor currently renders a local baseline workflow payload. The backend contains schema-validated workflow definition, revision, task, assignment, trigger, and execution log models.

Current editor panels:

- workflow metrics;
- triggers;
- workflow canvas;
- workflow properties;
- assignments;
- transitions;
- simulator;
- task inbox.

The Validate graph and Save draft buttons are present as baseline controls. Future persistence controls should use the same workflow schema and state-machine validation described in this guide.

## Workflow Metrics

The workflow summary shows:

- status, defaulting to `draft`;
- state count;
- transition count;
- trigger count.

Use these metrics as a quick check that the rendered workflow payload includes the expected graph structure before reviewing individual states and transitions.

## Triggers

Triggers come from the workflow payload `triggers` array.

Each trigger shows:

- trigger id;
- trigger type;
- source, or `no source` when one is not set.

Supported trigger types are:

- `form_submitted`;
- `entity_created`;
- `entity_updated`;
- `scheduled`;
- `manual`;
- `integration_webhook`.

Backend `WorkflowTrigger` records must reference a trigger that exists in the workflow revision payload. Trigger type and source are validated against the payload when trigger records are saved.

## Workflow Canvas

Workflow payloads are schema-backed state-machine definitions. Required top-level fields include `schema_version`, `workflow_id`, `name`, `version`, `initial_state`, `states`, and `triggers`.

Each canvas state shows:

- state id;
- label;
- state type;
- incoming transition count;
- outgoing transition count;
- assignment target when the state has an assignment.

Supported state types are:

- `start`;
- `task`;
- `approval`;
- `automated`;
- `end`.

The state-machine validator requires exactly one start state, and the `initial_state` must reference that start state.

## Properties And Assignments

The workflow properties panel summarizes:

- workflow id;
- version;
- initial state;
- schema version.

Assignment summaries are collected from states that define an assignment. Assignment types are:

- `role`;
- `user`;
- `expression`.

Each assignment type requires its matching target field and rejects inactive target fields. For example, a role assignment requires `role` and must not also set `user_id` or `expression`.

## Transitions

Transitions come from the workflow payload `transitions` array.

Each transition summary shows:

- transition id;
- label;
- trigger type;
- source state label;
- target state label;
- trigger id;
- guard expression, or `none` when no guard is set.

The state-machine validator checks that transition ids are unique, `from_state` and `to_state` reference defined states, and `trigger` references a defined trigger.

## Simulator

The simulator walks the workflow from `initial_state` by taking the first outgoing transition from each current state until no transition remains or a state repeats.

Each simulation step shows:

- step number;
- transition id;
- trigger id;
- source state label;
- target state label;
- guard expression.

The simulator marks the path complete when the final state is an `end` state. This is a baseline graph inspection aid; backend validation remains the source of truth for persisted workflow revisions.

## Task Inbox

The task inbox panel currently renders baseline task data for the displayed workflow.

The inbox summary shows:

- total task count;
- completed task count;
- overdue task count;
- active task count.

Task rows show:

- task key;
- subject;
- status;
- assignee;
- current state;
- due label.

Workflow task statuses are `open`, `in_progress`, `completed`, and `cancelled`. Active count includes `open` and `in_progress` tasks.

## Backend Models

Workflow definitions are tenant-scoped and identified by `workflow_id`.

Important backend records:

- `WorkflowDefinition`: tenant-scoped workflow identity and current revision pointer.
- `WorkflowRevision`: schema-validated payload version with `draft`, `reviewed`, `active`, or `archived` status.
- `WorkflowTask`: task instance tied to a workflow revision and current state.
- `WorkflowTaskAssignment`: role, user, or expression assignment for a task.
- `WorkflowTrigger`: persisted trigger tied to a workflow revision payload trigger.
- `WorkflowExecutionLog`: audit-style event log for workflow and task events.

Workflow tasks protect revision integrity. A task's current state must reference a state in its workflow revision payload, and task context must be a JSON object.

Execution log event types are:

- `workflow_started`;
- `task_created`;
- `task_assigned`;
- `transition_applied`;
- `task_completed`;
- `workflow_completed`.

## Validation

Workflow revision payload validation runs in two layers:

1. JSON schema validation for field shape, required fields, enum values, and nested objects.
2. State-machine validation for graph consistency.

State-machine validation checks:

- state ids are unique;
- trigger ids are unique;
- transition ids are unique;
- `initial_state` references a defined state;
- `initial_state` is a start state;
- exactly one start state exists;
- transitions reference known source states, target states, and triggers;
- every state is reachable from the initial state.

Fix schema errors first, then graph errors. Graph errors are easier to interpret once the payload shape is valid.

## Troubleshooting

If the workflow editor is not visible:

1. Confirm the user can access the Workflows module.
2. Confirm the route is `/workflows`.
3. Confirm the module registry still grants the route `workflows:manage`.

If transition labels or trigger types look wrong:

1. Confirm every transition references a trigger id in the payload `triggers` array.
2. Confirm every transition source and target references a state id in the payload `states` array.
3. Confirm state and trigger ids are unique.

If the simulator does not finish on an end state:

1. Confirm the graph has a path from `initial_state` to an `end` state.
2. Confirm the first outgoing transition from each state follows the intended happy path.
3. Confirm the workflow does not loop before reaching an end state.

If task records fail validation:

1. Confirm the task tenant matches the workflow and revision tenant.
2. Confirm the revision belongs to the workflow definition.
3. Confirm `current_state` references a state in the revision payload.
4. Confirm task context is a JSON object.

## Validation Commands

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Workflow builder behavior changes should also run:

```powershell
python tools/validate_backend.py
cd frontend-admin
npm run validate
```

Workflow schema changes should run:

```powershell
python contracts/validate_contracts.py
```
