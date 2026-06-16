import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  fetchFormDetail,
  getFormCanvasSections,
  getFormFieldPropertySummaries,
  getFormLogicRuleSummaries,
  getFormPayload,
  getFormPropertyRows,
  getFormToolboxItems,
  type FormDetail,
  type FormField,
  type FormFieldPropertySummary,
  type FormLogicRuleSummary,
  type FormPropertyRow
} from "../../api/formApi";

type FormDesignerState =
  | { form: FormDetail | null; status: "loading" }
  | { form: FormDetail; status: "loaded" }
  | { error: string; form: FormDetail | null; status: "error" };

export function FormDesignerView() {
  const { formId = "" } = useParams();
  const [state, setState] = useState<FormDesignerState>({ form: null, status: "loading" });

  const loadForm = useCallback(async () => {
    if (!formId) {
      setState({ error: "Form id is missing from the route.", form: null, status: "error" });
      return;
    }

    setState((current) => ({ form: current.form, status: "loading" }));
    try {
      const form = await fetchFormDetail(formId);
      setState({ form, status: "loaded" });
    } catch (error) {
      setState({
        error: error instanceof Error ? error.message : "Unable to load form.",
        form: null,
        status: "error"
      });
    }
  }, [formId]);

  useEffect(() => {
    void loadForm();
  }, [loadForm]);

  const payload = useMemo(() => (state.form ? getFormPayload(state.form) : undefined), [state.form]);
  const toolboxItems = useMemo(() => getFormToolboxItems(payload), [payload]);
  const canvasSections = useMemo(() => getFormCanvasSections(payload), [payload]);
  const formProperties = useMemo(() => getFormPropertyRows(payload), [payload]);
  const fieldProperties = useMemo(() => getFormFieldPropertySummaries(payload), [payload]);
  const logicRules = useMemo(() => getFormLogicRuleSummaries(payload), [payload]);

  return (
    <section className="form-designer-view" aria-labelledby="form-designer-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Form designer</p>
          <h2 id="form-designer-title">{state.form?.name ?? "Form canvas"}</h2>
        </div>
        <div className="theme-summary-actions">
          <Link className="button-link" to="/forms">
            Back to forms
          </Link>
          <button type="button" onClick={loadForm}>
            Refresh
          </button>
        </div>
      </div>

      {state.status === "loading" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Fetching form designer</h3>
        </section>
      ) : null}

      {state.status === "error" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Unavailable</p>
          <h3>Form designer could not load</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      {state.status === "loaded" && !payload ? (
        <section className="empty-state">
          <p className="eyebrow">No payload</p>
          <h3>No form payload is available</h3>
        </section>
      ) : null}

      {state.status === "loaded" && payload ? (
        <>
          <section className="metrics-grid" aria-label="Form designer summary">
            <article className="metric metric-good">
              <span>Status</span>
              <strong>{state.form.current_revision?.status ?? payload.status ?? "draft"}</strong>
            </article>
            <article className="metric">
              <span>Fields</span>
              <strong>{payload.fields.length}</strong>
            </article>
            <article className="metric">
              <span>Mode</span>
              <strong>{payload.mode}</strong>
            </article>
          </section>

          <section className="form-designer-grid" aria-label="Form designer">
            <aside className="form-toolbox" aria-label="Field toolbox">
              <h3>Field toolbox</h3>
              {toolboxItems.length > 0 ? (
                <div className="toolbox-list">
                  {toolboxItems.map((item) => (
                    <div className="toolbox-item" key={item.field_type}>
                      <strong>{item.label}</strong>
                      <span>{item.count} on canvas</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No field types available.</p>
              )}
            </aside>

            <section className="form-canvas" aria-label="Form canvas">
              {canvasSections.map((section) => (
                <article className="form-canvas-section" key={section.section_id}>
                  <div className="form-canvas-section-heading">
                    <p className="eyebrow">{section.section_id}</p>
                    <h3>{section.label}</h3>
                  </div>
                  <div className="form-field-stack">
                    {section.fields.map((field) => (
                      <CanvasField field={field} key={field.field_id} />
                    ))}
                  </div>
                </article>
              ))}
            </section>

            <aside className="form-properties-panel" aria-label="Form properties">
              <h3>Properties</h3>
              <PropertyRows rows={formProperties} />
              <div className="field-properties-list">
                {fieldProperties.map((field) => (
                  <FieldProperties field={field} key={field.field_id} />
                ))}
              </div>
            </aside>
          </section>

          <LogicPanel rules={logicRules} />
        </>
      ) : null}
    </section>
  );
}

type LogicPanelProps = {
  rules: FormLogicRuleSummary[];
};

function LogicPanel({ rules }: LogicPanelProps) {
  return (
    <section className="logic-panel" aria-label="Conditional logic">
      <div className="preview-panel-heading">
        <h3>Conditional logic</h3>
        <span className="queue-count">{rules.length} rules</span>
      </div>
      {rules.length > 0 ? (
        <div className="logic-rule-list">
          {rules.map((rule) => (
            <article className="logic-rule" key={`${rule.field_id}-${rule.kind}`}>
              <div>
                <p className="eyebrow">{rule.kind}</p>
                <h4>{rule.field_label}</h4>
              </div>
              <code>{rule.expression}</code>
              <span className="status status-draft">{rule.rule_type}</span>
            </article>
          ))}
        </div>
      ) : (
        <p>No conditional visibility or calculation rules are configured.</p>
      )}
    </section>
  );
}

type PropertyRowsProps = {
  rows: FormPropertyRow[];
};

function PropertyRows({ rows }: PropertyRowsProps) {
  return (
    <dl className="property-list">
      {rows.map((row) => (
        <div key={row.label}>
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

type FieldPropertiesProps = {
  field: FormFieldPropertySummary;
};

function FieldProperties({ field }: FieldPropertiesProps) {
  return (
    <article className="field-properties">
      <h4>{field.label}</h4>
      <PropertyRows rows={field.rows} />
    </article>
  );
}

type CanvasFieldProps = {
  field: FormField;
};

function CanvasField({ field }: CanvasFieldProps) {
  return (
    <article className="canvas-field">
      <div>
        <strong>{field.label}</strong>
        <span>{field.binding.data_path}</span>
      </div>
      <span className="status status-draft">{field.field_type}</span>
      {field.required ? <span className="status status-ready">required</span> : null}
    </article>
  );
}
