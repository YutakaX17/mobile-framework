import { type CSSProperties, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  fetchThemeDetail,
  getAssetTokenRows,
  getColorTokenRows,
  getModeRows,
  getNumberTokenRows,
  getThemePayload,
  getTypographyTokenRows,
  type ThemeDetail,
  type ThemeTokenRow
} from "../../api/themeApi";
import { formatContrastRatio, getThemeContrastChecks, type ContrastCheck } from "../themeContrast";
import {
  getThemePreviewModeOptions,
  resolveThemePreviewTokens,
  type ThemePreviewTokens
} from "../themePreview";

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
  const modeOptions = useMemo(() => getThemePreviewModeOptions(payload), [payload]);
  const [selectedModeId, setSelectedModeId] = useState("");
  const previewTokens = useMemo(
    () => resolveThemePreviewTokens(payload, selectedModeId || modeOptions[0]?.id),
    [modeOptions, payload, selectedModeId]
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
            <ThemePreviewPanel
              modeOptions={modeOptions}
              onModeChange={setSelectedModeId}
              selectedModeId={selectedModeId || modeOptions[0]?.id || ""}
              tokens={previewTokens}
            />
            <TokenPanel title="Assets" rows={getAssetTokenRows(payload)} />
            <TokenPanel title="Colors" rows={getColorTokenRows(payload)} />
            <TokenPanel title="Typography" rows={getTypographyTokenRows(payload)} />
            <TokenPanel title="Spacing" rows={getNumberTokenRows(payload, "spacing")} />
            <TokenPanel title="Radius" rows={getNumberTokenRows(payload, "radius")} />
            <TokenPanel title="Modes" rows={getModeRows(payload)} />
            <ContrastPanel checks={getThemeContrastChecks(payload)} />
          </section>
        </>
      ) : null}
    </section>
  );
}

type ThemePreviewPanelProps = {
  modeOptions: { id: string; label: string }[];
  onModeChange: (modeId: string) => void;
  selectedModeId: string;
  tokens: ThemePreviewTokens;
};

function ThemePreviewPanel({ modeOptions, onModeChange, selectedModeId, tokens }: ThemePreviewPanelProps) {
  const previewStyle = {
    "--preview-background": tokens.background,
    "--preview-primary": tokens.primary,
    "--preview-radius": `${tokens.borderRadius}px`,
    "--preview-surface": tokens.surface,
    "--preview-text": tokens.text,
    color: tokens.text,
    fontFamily: tokens.fontFamily,
    padding: tokens.padding
  } as CSSProperties;

  return (
    <article className="token-panel preview-panel">
      <div className="preview-panel-heading">
        <h3>Live preview</h3>
        {modeOptions.length > 0 ? (
          <select
            aria-label="Preview mode"
            onChange={(event) => onModeChange(event.target.value)}
            value={selectedModeId}
          >
            {modeOptions.map((mode) => (
              <option key={mode.id} value={mode.id}>
                {mode.label}
              </option>
            ))}
          </select>
        ) : null}
      </div>
      <div className="theme-preview" style={previewStyle}>
        <section>
          <p>Mobile screen</p>
          <h4>Field Operations</h4>
          <span>3 tasks ready</span>
          <button type="button">Start review</button>
        </section>
      </div>
    </article>
  );
}

type ContrastPanelProps = {
  checks: ContrastCheck[];
};

function ContrastPanel({ checks }: ContrastPanelProps) {
  return (
    <article className="token-panel contrast-panel">
      <h3>Contrast</h3>
      {checks.length > 0 ? (
        <div className="contrast-checks">
          {checks.map((check) => (
            <div className="contrast-check" key={`${check.label}-${check.foreground}-${check.background}`}>
              <div>
                <strong>{check.label}</strong>
                <span>{formatContrastRatio(check.ratio)}</span>
              </div>
              <div className="contrast-swatches" aria-hidden="true">
                <span style={{ backgroundColor: check.background }} />
                <span style={{ backgroundColor: check.foreground }} />
              </div>
              <span className={`status ${check.passesAA ? "status-ready" : "status-blocked"}`}>
                {check.passesAAA ? "AAA" : check.passesAA ? "AA" : "Fail"}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p>No contrast pairs available.</p>
      )}
    </article>
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
