import { describe, expect, it } from "vitest";

import {
  getWorkflowAssignmentSummaries,
  getWorkflowCanvasStates,
  getWorkflowEditorMetrics,
  getWorkflowTransitionSummaries,
  simulateWorkflowPath,
  workflowEditorPayload
} from "./workflowEditorModel";

describe("workflow editor model", () => {
  it("builds canvas state connection counts", () => {
    expect(getWorkflowCanvasStates(workflowEditorPayload)).toEqual([
      expect.objectContaining({ incoming_count: 0, outgoing_count: 1, state_id: "submitted" }),
      expect.objectContaining({ incoming_count: 1, outgoing_count: 1, state_id: "triage_review" }),
      expect.objectContaining({ incoming_count: 1, outgoing_count: 0, state_id: "approved" })
    ]);
  });

  it("summarizes transitions with labels and trigger type", () => {
    expect(getWorkflowTransitionSummaries(workflowEditorPayload)[0]).toMatchObject({
      from_label: "Submitted",
      to_label: "Triage review",
      trigger_type: "form_submitted"
    });
  });

  it("summarizes assignments and metrics", () => {
    expect(getWorkflowAssignmentSummaries(workflowEditorPayload)).toEqual([
      {
        state_id: "triage_review",
        state_label: "Triage review",
        target: "clinical.triage",
        type: "role"
      }
    ]);
    expect(getWorkflowEditorMetrics(workflowEditorPayload).map((metric) => metric.value)).toEqual([
      "draft",
      "3",
      "2",
      "2"
    ]);
  });

  it("simulates the default workflow path to a terminal state", () => {
    expect(simulateWorkflowPath(workflowEditorPayload)).toEqual({
      final_state: "approved",
      final_state_label: "Approved",
      is_complete: true,
      steps: [
        {
          from_label: "Submitted",
          guard: "none",
          step: 1,
          to_label: "Triage review",
          transition_id: "submit_for_review",
          trigger: "intake_submitted"
        },
        {
          from_label: "Triage review",
          guard: "approval.decision == 'approved'",
          step: 2,
          to_label: "Approved",
          transition_id: "approve_intake",
          trigger: "manual_approval"
        }
      ]
    });
  });
});
