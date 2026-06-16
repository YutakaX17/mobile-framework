import { useCallback, useEffect, useMemo, useState } from "react";

import { countFormsByStatus, fetchFormSummaries, type FormSummary } from "../../api/formApi";

type FormListState =
  | { forms: FormSummary[]; status: "loading" }
  | { forms: FormSummary[]; status: "loaded" }
  | { error: string; forms: FormSummary[]; status: "error" };

export function FormListView() {
  const [state, setState] = useState<FormListState>({ forms: [], status: "loading" });

  const loadForms = useCallback(async () => {
    setState((current) => ({ forms: current.forms, status: "loading" }));
    try {
      const forms = await fetchFormSummaries();
      setState({ forms, status: "loaded" });
    } catch (error) {
      setState({
        error: error instanceof Error ? error.message : "Unable to load forms.",
        forms: [],
        status: "error"
      });
    }
  }, []);

  useEffect(() => {
    void loadForms();
  }, [loadForms]);

  const publishedCount = useMemo(() => countFormsByStatus(state.forms, "published"), [state.forms]);
  const fieldCount = useMemo(
    () => state.forms.reduce((total, form) => total + (form.current_revision?.field_count ?? 0), 0),
    [state.forms]
  );

  return (
    <section className="form-list-view" aria-labelledby="form-list-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Form builder</p>
          <h2 id="form-list-title">Form library</h2>
        </div>
        <div className="theme-summary-actions">
          <span className="queue-count">{state.forms.length} forms</span>
          <button type="button" onClick={loadForms}>
            Refresh
          </button>
        </div>
      </div>

      {state.status === "loading" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Fetching forms</h3>
        </section>
      ) : null}

      {state.status === "error" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Unavailable</p>
          <h3>Form list could not load</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      {state.status === "loaded" && state.forms.length === 0 ? (
        <section className="empty-state">
          <p className="eyebrow">No forms</p>
          <h3>No forms available</h3>
        </section>
      ) : null}

      {state.status === "loaded" && state.forms.length > 0 ? (
        <>
          <section className="metrics-grid" aria-label="Form summary">
            <article className="metric metric-good">
              <span>Published forms</span>
              <strong>{publishedCount}</strong>
            </article>
            <article className="metric">
              <span>Total fields</span>
              <strong>{fieldCount}</strong>
            </article>
          </section>

          <section className="form-list" aria-label="Forms">
            {state.forms.map((form) => (
              <article className="form-card" key={form.form_id}>
                <div>
                  <p className="eyebrow">{form.form_id}</p>
                  <h3>{form.name}</h3>
                  {form.description ? <p>{form.description}</p> : null}
                </div>
                <dl className="theme-meta">
                  <div>
                    <dt>Status</dt>
                    <dd>
                      <span className={`status status-${form.current_revision?.status ?? "draft"}`}>
                        {form.current_revision?.status ?? "draft"}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>Mode</dt>
                    <dd>{form.mode}</dd>
                  </div>
                  <div>
                    <dt>Version</dt>
                    <dd>{form.current_revision?.version ?? "unversioned"}</dd>
                  </div>
                  <div>
                    <dt>Fields</dt>
                    <dd>{form.current_revision?.field_count ?? 0}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </section>
        </>
      ) : null}
    </section>
  );
}
