import {
  getWorkflowAssignmentSummaries,
  getWorkflowCanvasStates,
  getWorkflowEditorMetrics,
  getWorkflowTransitionSummaries,
  simulateWorkflowPath,
  workflowEditorPayload,
  type WorkflowAssignmentSummary,
  type WorkflowCanvasState,
  type WorkflowSimulationResult,
  type WorkflowTransitionSummary,
  type WorkflowTrigger
} from "../../builders/workflowEditorModel";

export function WorkflowEditorView() {
  const payload = workflowEditorPayload;
  const metrics = getWorkflowEditorMetrics(payload);
  const states = getWorkflowCanvasStates(payload);
  const transitions = getWorkflowTransitionSummaries(payload);
  const assignments = getWorkflowAssignmentSummaries(payload);
  const simulation = simulateWorkflowPath(payload);

  return (
    <section className="workflow-editor-view" aria-labelledby="workflow-editor-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workflow editor</p>
          <h2 id="workflow-editor-title">{payload.name}</h2>
        </div>
        <div className="theme-summary-actions">
          <button type="button">Validate graph</button>
          <button className="primary-action" type="button">
            Save draft
          </button>
        </div>
      </div>

      <section className="metrics-grid" aria-label="Workflow editor summary">
        {metrics.map((metric) => (
          <article className={metric.label === "Status" ? "metric metric-good" : "metric"} key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="workflow-editor-grid" aria-label="Workflow visual editor">
        <aside className="form-toolbox" aria-label="Workflow triggers">
          <h3>Triggers</h3>
          <TriggerList triggers={payload.triggers} />
        </aside>

        <section className="workflow-canvas" aria-label="Workflow canvas">
          {states.map((state) => (
            <WorkflowStateCard state={state} key={state.state_id} />
          ))}
        </section>

        <aside className="form-properties-panel" aria-label="Workflow properties">
          <h3>Properties</h3>
          <dl className="property-list">
            <div>
              <dt>Workflow id</dt>
              <dd>{payload.workflow_id}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{payload.version}</dd>
            </div>
            <div>
              <dt>Initial state</dt>
              <dd>{payload.initial_state}</dd>
            </div>
            <div>
              <dt>Schema</dt>
              <dd>{payload.schema_version}</dd>
            </div>
          </dl>
          <AssignmentList assignments={assignments} />
        </aside>
      </section>

      <TransitionPanel transitions={transitions} />
      <SimulationPanel simulation={simulation} />
    </section>
  );
}

type WorkflowStateCardProps = {
  state: WorkflowCanvasState;
};

function WorkflowStateCard({ state }: WorkflowStateCardProps) {
  return (
    <article className={`workflow-state-card workflow-state-${state.state_type}`}>
      <div className="form-canvas-section-heading">
        <p className="eyebrow">{state.state_id}</p>
        <h3>{state.label}</h3>
      </div>
      <div className="screen-card-footer">
        <span className="status status-draft">{state.state_type}</span>
        <span className="queue-count">{state.incoming_count} in</span>
        <span className="queue-count">{state.outgoing_count} out</span>
      </div>
      {state.assignment ? (
        <dl className="theme-meta">
          <div>
            <dt>Assignment</dt>
            <dd>{state.assignment.role ?? state.assignment.user_id ?? state.assignment.expression}</dd>
          </div>
        </dl>
      ) : null}
    </article>
  );
}

type TriggerListProps = {
  triggers: WorkflowTrigger[];
};

function TriggerList({ triggers }: TriggerListProps) {
  return (
    <div className="toolbox-list">
      {triggers.map((trigger) => (
        <div className="toolbox-item" key={trigger.trigger_id}>
          <strong>{trigger.trigger_id}</strong>
          <span>
            {trigger.trigger_type} - {trigger.source ?? "no source"}
          </span>
        </div>
      ))}
    </div>
  );
}

type AssignmentListProps = {
  assignments: WorkflowAssignmentSummary[];
};

function AssignmentList({ assignments }: AssignmentListProps) {
  return (
    <section className="field-properties-list" aria-label="Workflow assignments">
      <h3>Assignments</h3>
      {assignments.map((assignment) => (
        <article className="field-properties" key={assignment.state_id}>
          <p className="eyebrow">{assignment.type}</p>
          <h4>{assignment.state_label}</h4>
          <dl className="property-list">
            <div>
              <dt>Target</dt>
              <dd>{assignment.target}</dd>
            </div>
          </dl>
        </article>
      ))}
    </section>
  );
}

type TransitionPanelProps = {
  transitions: WorkflowTransitionSummary[];
};

function TransitionPanel({ transitions }: TransitionPanelProps) {
  return (
    <section className="validation-panel" aria-label="Workflow transitions">
      <div className="preview-panel-heading">
        <h3>Transitions</h3>
        <span className="queue-count">{transitions.length} transitions</span>
      </div>
      <div className="validation-rule-list">
        {transitions.map((transition) => (
          <article className="validation-rule action-binding-rule" key={transition.transition_id}>
            <div>
              <p className="eyebrow">{transition.transition_id}</p>
              <h4>{transition.label ?? transition.transition_id}</h4>
            </div>
            <strong>{transition.trigger_type}</strong>
            <dl className="action-binding-meta">
              <div>
                <dt>From</dt>
                <dd>{transition.from_label}</dd>
              </div>
              <div>
                <dt>To</dt>
                <dd>{transition.to_label}</dd>
              </div>
              <div>
                <dt>Trigger</dt>
                <dd>{transition.trigger}</dd>
              </div>
              <div>
                <dt>Guard</dt>
                <dd>{transition.guard ?? "none"}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

type SimulationPanelProps = {
  simulation: WorkflowSimulationResult;
};

function SimulationPanel({ simulation }: SimulationPanelProps) {
  return (
    <section className="validation-panel" aria-label="Workflow simulator">
      <div className="preview-panel-heading">
        <h3>Simulator</h3>
        <span className={simulation.is_complete ? "status status-ready" : "status status-draft"}>
          {simulation.final_state_label}
        </span>
      </div>
      <div className="validation-rule-list">
        {simulation.steps.map((step) => (
          <article className="validation-rule action-binding-rule" key={step.transition_id}>
            <div>
              <p className="eyebrow">Step {step.step}</p>
              <h4>{step.transition_id}</h4>
            </div>
            <strong>{step.trigger}</strong>
            <dl className="action-binding-meta">
              <div>
                <dt>From</dt>
                <dd>{step.from_label}</dd>
              </div>
              <div>
                <dt>To</dt>
                <dd>{step.to_label}</dd>
              </div>
              <div>
                <dt>Guard</dt>
                <dd>{step.guard}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
