import { useCallback, useEffect, useMemo, useState } from "react";

import { countThemesByStatus, fetchThemeSummaries, type ThemeSummary } from "../../api/themeApi";

type ThemeListState =
  | { status: "loading"; themes: ThemeSummary[] }
  | { status: "loaded"; themes: ThemeSummary[] }
  | { error: string; status: "error"; themes: ThemeSummary[] };

export function ThemeListView() {
  const [state, setState] = useState<ThemeListState>({ status: "loading", themes: [] });

  const loadThemes = useCallback(async () => {
    setState((current) => ({ status: "loading", themes: current.themes }));
    try {
      const themes = await fetchThemeSummaries();
      setState({ status: "loaded", themes });
    } catch (error) {
      setState({
        error: error instanceof Error ? error.message : "Unable to load themes.",
        status: "error",
        themes: []
      });
    }
  }, []);

  useEffect(() => {
    void loadThemes();
  }, [loadThemes]);

  const publishedCount = useMemo(() => countThemesByStatus(state.themes, "published"), [state.themes]);

  return (
    <section className="theme-list-view" aria-labelledby="theme-list-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Theme builder</p>
          <h2 id="theme-list-title">Theme library</h2>
        </div>
        <div className="theme-summary-actions">
          <span className="queue-count">{state.themes.length} themes</span>
          <button type="button" onClick={loadThemes}>
            Refresh
          </button>
        </div>
      </div>

      {state.status === "loading" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Fetching themes</h3>
        </section>
      ) : null}

      {state.status === "error" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Unavailable</p>
          <h3>Theme list could not load</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      {state.status === "loaded" && state.themes.length === 0 ? (
        <section className="empty-state">
          <p className="eyebrow">No themes</p>
          <h3>No themes available</h3>
        </section>
      ) : null}

      {state.status === "loaded" && state.themes.length > 0 ? (
        <>
          <section className="metrics-grid" aria-label="Theme summary">
            <article className="metric metric-good">
              <span>Published themes</span>
              <strong>{publishedCount}</strong>
            </article>
            <article className="metric">
              <span>Total themes</span>
              <strong>{state.themes.length}</strong>
            </article>
          </section>

          <section className="theme-list" aria-label="Themes">
            {state.themes.map((theme) => (
              <article className="theme-card" key={theme.theme_id}>
                <div>
                  <p className="eyebrow">{theme.theme_id}</p>
                  <h3>{theme.name}</h3>
                  {theme.description ? <p>{theme.description}</p> : null}
                </div>
                <dl className="theme-meta">
                  <div>
                    <dt>Status</dt>
                    <dd>
                      <span className={`status status-${theme.current_revision?.status ?? "draft"}`}>
                        {theme.current_revision?.status ?? "draft"}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt>Version</dt>
                    <dd>{theme.current_revision?.version ?? "unversioned"}</dd>
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
