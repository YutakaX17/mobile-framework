import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  fetchThemeDetail,
  getColorTokenRows,
  getModeRows,
  getNumberTokenRows,
  getThemePayload,
  getTypographyTokenRows,
  type ThemeDetail,
  type ThemeTokenRow
} from "../../api/themeApi";

type ThemeDetailState =
  | { status: "loading"; theme: ThemeDetail | null }
  | { status: "loaded"; theme: ThemeDetail }
  | { error: string; status: "error"; theme: ThemeDetail | null };

export function ThemeDetailView() {
  const { themeId = "" } = useParams();
  const [state, setState] = useState<ThemeDetailState>({ status: "loading", theme: null });

  const loadTheme = useCallback(async () => {
    if (!themeId) {
      setState({ error: "Theme id is missing from the route.", status: "error", theme: null });
      return;
    }

    setState((current) => ({ status: "loading", theme: current.theme }));
    try {
      const theme = await fetchThemeDetail(themeId);
      setState({ status: "loaded", theme });
    } catch (error) {
      setState({
        error: error instanceof Error ? error.message : "Unable to load theme.",
        status: "error",
        theme: null
      });
    }
  }, [themeId]);

  useEffect(() => {
    void loadTheme();
  }, [loadTheme]);

  const payload = useMemo(
    () => (state.theme ? getThemePayload(state.theme) : undefined),
    [state.theme]
  );

  return (
    <section className="theme-detail-view" aria-labelledby="theme-detail-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Theme editor</p>
          <h2 id="theme-detail-title">{state.theme?.name ?? "Theme tokens"}</h2>
        </div>
        <div className="theme-summary-actions">
          <Link className="button-link" to="/themes">
            Back to themes
          </Link>
          <button type="button" onClick={loadTheme}>
            Refresh
          </button>
        </div>
      </div>

      {state.status === "loading" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Fetching theme tokens</h3>
        </section>
      ) : null}

      {state.status === "error" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Unavailable</p>
          <h3>Theme could not load</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      {state.status === "loaded" && !payload ? (
        <section className="empty-state">
          <p className="eyebrow">No payload</p>
          <h3>No token payload is available</h3>
        </section>
      ) : null}

      {state.status === "loaded" && payload ? (
        <>
          <section className="metrics-grid" aria-label="Theme revision summary">
            <article className="metric metric-good">
              <span>Status</span>
              <strong>{state.theme.current_revision?.status ?? "draft"}</strong>
            </article>
            <article className="metric">
              <span>Version</span>
              <strong>{state.theme.current_revision?.version ?? payload.version}</strong>
            </article>
          </section>

          <section className="token-panel-grid" aria-label="Theme tokens">
            <TokenPanel title="Colors" rows={getColorTokenRows(payload)} />
            <TokenPanel title="Typography" rows={getTypographyTokenRows(payload)} />
            <TokenPanel title="Spacing" rows={getNumberTokenRows(payload, "spacing")} />
            <TokenPanel title="Radius" rows={getNumberTokenRows(payload, "radius")} />
            <TokenPanel title="Modes" rows={getModeRows(payload)} />
          </section>
        </>
      ) : null}
    </section>
  );
}

type TokenPanelProps = {
  rows: ThemeTokenRow[];
  title: string;
};

function TokenPanel({ rows, title }: TokenPanelProps) {
  return (
    <article className="token-panel">
      <h3>{title}</h3>
      {rows.length > 0 ? (
        <dl>
          {rows.map((row) => (
            <div key={row.label}>
              <dt>{row.label}</dt>
              <dd>
                <strong>{row.value}</strong>
                {row.detail ? <span>{row.detail}</span> : null}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p>No tokens available.</p>
      )}
    </article>
  );
}
