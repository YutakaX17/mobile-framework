import { describe, expect, it } from "vitest";

import {
  getWorkflowAssignmentSummaries,
  getWorkflowCanvasStates,
  getWorkflowEditorMetrics,
  getWorkflowTransitionSummaries,
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
});
