export type WorkflowAssignment = {
  assignment_type: "role" | "user" | "expression";
  expression?: string;
  role?: string;
  user_id?: string;
};

export type WorkflowState = {
  assignment?: WorkflowAssignment;
  label: string;
  state_id: string;
  state_type: "start" | "task" | "approval" | "automated" | "end";
};

export type WorkflowTransition = {
  from_state: string;
  guard?: string;
  label?: string;
  to_state: string;
  transition_id: string;
  trigger: string;
};

export type WorkflowTrigger = {
  source?: string;
  trigger_id: string;
  trigger_type: "form_submitted" | "entity_created" | "entity_updated" | "scheduled" | "manual" | "integration_webhook";
};

export type WorkflowEditorPayload = {
  initial_state: string;
  name: string;
  schema_version: "v1";
  states: WorkflowState[];
  status?: "draft" | "active" | "archived";
  transitions?: WorkflowTransition[];
  triggers: WorkflowTrigger[];
  version: string;
  workflow_id: string;
};

export type WorkflowCanvasState = WorkflowState & {
  incoming_count: number;
  outgoing_count: number;
};

export type WorkflowTransitionSummary = WorkflowTransition & {
  from_label: string;
  to_label: string;
  trigger_type: string;
};

export type WorkflowAssignmentSummary = {
  state_id: string;
  state_label: string;
  target: string;
  type: WorkflowAssignment["assignment_type"];
};

export type WorkflowEditorMetric = {
  label: string;
  value: string;
};

export const workflowEditorPayload: WorkflowEditorPayload = {
  initial_state: "submitted",
  name: "Patient intake approval",
  schema_version: "v1",
  status: "draft",
  version: "1.0.0",
  workflow_id: "patient_intake_approval",
  states: [
    {
      label: "Submitted",
      state_id: "submitted",
      state_type: "start"
    },
    {
      assignment: {
        assignment_type: "role",
        role: "clinical.triage"
      },
      label: "Triage review",
      state_id: "triage_review",
      state_type: "approval"
    },
    {
      label: "Approved",
      state_id: "approved",
      state_type: "end"
    }
  ],
  transitions: [
    {
      from_state: "submitted",
      label: "Submit for review",
      to_state: "triage_review",
      transition_id: "submit_for_review",
      trigger: "intake_submitted"
    },
    {
      from_state: "triage_review",
      guard: "approval.decision == 'approved'",
      label: "Approve intake",
      to_state: "approved",
      transition_id: "approve_intake",
      trigger: "manual_approval"
    }
  ],
  triggers: [
    {
      source: "patient_intake",
      trigger_id: "intake_submitted",
      trigger_type: "form_submitted"
    },
    {
      source: "triage_review",
      trigger_id: "manual_approval",
      trigger_type: "manual"
    }
  ]
};

export function getWorkflowCanvasStates(payload: WorkflowEditorPayload): WorkflowCanvasState[] {
  const transitions = payload.transitions ?? [];

  return payload.states.map((state) => ({
    ...state,
    incoming_count: transitions.filter((transition) => transition.to_state === state.state_id).length,
    outgoing_count: transitions.filter((transition) => transition.from_state === state.state_id).length
  }));
}

export function getWorkflowTransitionSummaries(payload: WorkflowEditorPayload): WorkflowTransitionSummary[] {
  const statesById = new Map(payload.states.map((state) => [state.state_id, state]));
  const triggersById = new Map(payload.triggers.map((trigger) => [trigger.trigger_id, trigger]));

  return (payload.transitions ?? []).map((transition) => ({
    ...transition,
    from_label: statesById.get(transition.from_state)?.label ?? transition.from_state,
    to_label: statesById.get(transition.to_state)?.label ?? transition.to_state,
    trigger_type: triggersById.get(transition.trigger)?.trigger_type ?? "unknown"
  }));
}

export function getWorkflowAssignmentSummaries(payload: WorkflowEditorPayload): WorkflowAssignmentSummary[] {
  return payload.states
    .filter((state) => state.assignment)
    .map((state) => {
      const assignment = state.assignment as WorkflowAssignment;
      return {
        state_id: state.state_id,
        state_label: state.label,
        target: assignment.role ?? assignment.user_id ?? assignment.expression ?? "unassigned",
        type: assignment.assignment_type
      };
    });
}

export function getWorkflowEditorMetrics(payload: WorkflowEditorPayload): WorkflowEditorMetric[] {
  return [
    { label: "Status", value: payload.status ?? "draft" },
    { label: "States", value: String(payload.states.length) },
    { label: "Transitions", value: String(payload.transitions?.length ?? 0) },
    { label: "Triggers", value: String(payload.triggers.length) }
  ];
}
