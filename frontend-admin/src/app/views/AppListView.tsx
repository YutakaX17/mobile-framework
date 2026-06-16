import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { countAppsByStatus, fetchAppSummaries, type AppSummary } from "../../api/appApi";

type AppListState =
  | { apps: AppSummary[]; status: "loading" }
  | { apps: AppSummary[]; status: "loaded" }
  | { apps: AppSummary[]; error: string; status: "error" };

export function AppListView() {
  const [state, setState] = useState<AppListState>({ apps: [], status: "loading" });

  const loadApps = useCallback(async () => {
    setState((current) => ({ apps: current.apps, status: "loading" }));
    try {
      const apps = await fetchAppSummaries();
      setState({ apps, status: "loaded" });
    } catch (error) {
      setState({
        apps: [],
        error: error instanceof Error ? error.message : "Unable to load apps.",
        status: "error"
      });
    }
  }, []);

  useEffect(() => {
    void loadApps();
  }, [loadApps]);

  const publishedCount = useMemo(() => countAppsByStatus(state.apps, "published"), [state.apps]);
  const screenCount = useMemo(
    () => state.apps.reduce((total, app) => total + (app.current_revision?.screen_count ?? 0), 0),
    [state.apps]
  );
  const navigationCount = useMemo(
    () => state.apps.reduce((total, app) => total + (app.current_revision?.navigation_count ?? 0), 0),
    [state.apps]
  );

  return (
    <section className="app-list-view" aria-labelledby="app-list-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">App builder</p>
          <h2 id="app-list-title">App library</h2>
        </div>
        <div className="theme-summary-actions">
          <span className="queue-count">{state.apps.length} apps</span>
          <button type="button" onClick={loadApps}>
            Refresh
          </button>
        </div>
      </div>

      {state.status === "loading" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Fetching apps</h3>
        </section>
      ) : null}

      {state.status === "error" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Unavailable</p>
          <h3>App list could not load</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      {state.status === "loaded" && state.apps.length === 0 ? (
        <section className="empty-state">
          <p className="eyebrow">No apps</p>
          <h3>No apps available</h3>
        </section>
      ) : null}

      {state.status === "loaded" && state.apps.length > 0 ? (
        <>
          <section className="metrics-grid" aria-label="App summary">
            <article className="metric metric-good">
              <span>Published apps</span>
              <strong>{publishedCount}</strong>
            </article>
            <article className="metric">
              <span>Total screens</span>
              <strong>{screenCount}</strong>
            </article>
            <article className="metric">
              <span>Navigation items</span>
              <strong>{navigationCount}</strong>
            </article>
          </section>

          <section className="app-list" aria-label="Apps">
            {state.apps.map((app) => (
              <article className="app-card" key={app.app_id}>
                <div>
                  <p className="eyebrow">{app.app_id}</p>
                  <h3>
                    <Link to={`/apps/${app.app_id}`}>{app.name}</Link>
                  </h3>
                  {app.description ? <p>{app.description}</p> : null}
                </div>
                <dl className="theme-meta">
                  <div>
                    <dt>Status</dt>
                    <dd>
                      <span className={`status status-${app.current_revision?.status ?? "draft"}`}>
                        {app.current_revision?.status ?? "draft"}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>Version</dt>
                    <dd>{app.current_revision?.version ?? "unversioned"}</dd>
                  </div>
                  <div>
                    <dt>Screens</dt>
                    <dd>{app.current_revision?.screen_count ?? 0}</dd>
                  </div>
                  <div>
                    <dt>Permissions</dt>
                    <dd>{app.current_revision?.permission_count ?? 0}</dd>
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
