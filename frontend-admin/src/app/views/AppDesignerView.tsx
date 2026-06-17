import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getComponentToolboxItems, type ComponentToolboxItem } from "../../builders/appComponentRegistry";
import {
  fetchAppDetail,
  getAppActionSummaries,
  getAppCanvasScreens,
  getAppComponentPropertySummaries,
  getAppPayload,
  type AppActionSummary,
  type AppCanvasScreen,
  type AppComponent,
  type AppComponentPropertySummary,
  type AppDetail,
  type AppNavigationItem
} from "../../api/appApi";

type AppDesignerState =
  | { app: AppDetail | null; status: "loading" }
  | { app: AppDetail; status: "loaded" }
  | { app: AppDetail | null; error: string; status: "error" };

export function AppDesignerView() {
  const { appId = "" } = useParams();
  const [state, setState] = useState<AppDesignerState>({ app: null, status: "loading" });

  const loadApp = useCallback(async () => {
    if (!appId) {
      setState({ app: null, error: "App id is missing from the route.", status: "error" });
      return;
    }

    setState((current) => ({ app: current.app, status: "loading" }));
    try {
      const app = await fetchAppDetail(appId);
      setState({ app, status: "loaded" });
    } catch (error) {
      setState({
        app: null,
        error: error instanceof Error ? error.message : "Unable to load app.",
        status: "error"
      });
    }
  }, [appId]);

  useEffect(() => {
    void loadApp();
  }, [loadApp]);

  const payload = useMemo(() => (state.app ? getAppPayload(state.app) : undefined), [state.app]);
  const screens = useMemo(() => getAppCanvasScreens(payload), [payload]);
  const actions = useMemo(() => getAppActionSummaries(payload), [payload]);
  const componentProperties = useMemo(() => getAppComponentPropertySummaries(payload), [payload]);
  const componentToolboxItems = useMemo(() => getComponentToolboxItems(payload), [payload]);

  return (
    <section className="app-designer-view" aria-labelledby="app-designer-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">App builder</p>
          <h2 id="app-designer-title">{state.app?.name ?? "Screen canvas"}</h2>
        </div>
        <div className="theme-summary-actions">
          <Link className="button-link" to="/apps">
            Back to apps
          </Link>
          <button type="button" onClick={loadApp}>
            Refresh
          </button>
        </div>
      </div>

      {state.status === "loading" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Fetching app builder</h3>
        </section>
      ) : null}

      {state.status === "error" ? (
        <section className="empty-state" aria-live="polite">
          <p className="eyebrow">Unavailable</p>
          <h3>App builder could not load</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      {state.status === "loaded" && !payload ? (
        <section className="empty-state">
          <p className="eyebrow">No payload</p>
          <h3>No app payload is available</h3>
        </section>
      ) : null}

      {state.status === "loaded" && payload ? (
        <>
          <section className="metrics-grid" aria-label="App builder summary">
            <article className="metric metric-good">
              <span>Status</span>
              <strong>{state.app.current_revision?.status ?? "draft"}</strong>
            </article>
            <article className="metric">
              <span>Screens</span>
              <strong>{screens.length}</strong>
            </article>
            <article className="metric">
              <span>Navigation</span>
              <strong>{payload.navigation.length}</strong>
            </article>
            <article className="metric">
              <span>Actions</span>
              <strong>{actions.length}</strong>
            </article>
          </section>

          <section className="app-designer-grid" aria-label="App screen builder">
            <aside className="form-toolbox" aria-label="Navigation">
              <h3>Navigation</h3>
              <NavigationList items={payload.navigation} />
              <ComponentRegistryList items={componentToolboxItems} />
            </aside>

            <section className="app-screen-canvas" aria-label="Screen canvas">
              {screens.map((screen) => (
                <ScreenCanvasCard screen={screen} key={screen.screen_id} />
              ))}
            </section>

            <aside className="form-properties-panel" aria-label="App properties">
              <h3>Properties</h3>
              <dl className="property-list">
                <div>
                  <dt>App id</dt>
                  <dd>{payload.app_id}</dd>
                </div>
                <div>
                  <dt>Version</dt>
                  <dd>{payload.version}</dd>
                </div>
                <div>
                  <dt>Theme</dt>
                  <dd>{payload.theme_id ?? "not set"}</dd>
                </div>
                <div>
                  <dt>Permissions</dt>
                  <dd>{payload.permissions?.length ?? 0}</dd>
                </div>
              </dl>
              <ComponentPropertiesList items={componentProperties} />
            </aside>
          </section>

          <ActionPanel actions={actions} />
        </>
      ) : null}
    </section>
  );
}

type ComponentRegistryListProps = {
  items: ComponentToolboxItem[];
};

function ComponentRegistryList({ items }: ComponentRegistryListProps) {
  return (
    <section className="component-registry-list" aria-label="Component registry">
      <h3>Components</h3>
      <div className="toolbox-list">
        {items.map((item) => (
          <div className="toolbox-item" key={item.component_type}>
            <strong>{item.label}</strong>
            <span>
              {item.summary} - {item.count} on canvas
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

type NavigationListProps = {
  items: AppNavigationItem[];
};

function NavigationList({ items }: NavigationListProps) {
  if (items.length === 0) {
    return <p>No navigation items are configured.</p>;
  }

  return (
    <div className="toolbox-list">
      {items.map((item) => (
        <div className="toolbox-item" key={`${item.screen_id}-${item.label}`}>
          <strong>{item.label}</strong>
          <span>{formatNavigationMeta(item)}</span>
        </div>
      ))}
    </div>
  );
}

function formatNavigationMeta(item: AppNavigationItem): string {
  const parts = [
    item.screen_id,
    item.group ?? "primary",
    item.presentation ?? "drawer",
    `order ${item.order ?? 0}`
  ];

  if (item.is_default) {
    parts.push("default");
  }

  return parts.join(" - ");
}

type ScreenCanvasCardProps = {
  screen: AppCanvasScreen;
};

function ScreenCanvasCard({ screen }: ScreenCanvasCardProps) {
  return (
    <article className="app-screen-card">
      <div className="form-canvas-section-heading">
        <p className="eyebrow">{screen.screen_id}</p>
        <h3>{screen.name}</h3>
      </div>
      <dl className="theme-meta">
        <div>
          <dt>Type</dt>
          <dd>{screen.screen_type}</dd>
        </div>
        <div>
          <dt>Order</dt>
          <dd>{screen.order}</dd>
        </div>
        <div>
          <dt>Route</dt>
          <dd>{screen.route}</dd>
        </div>
        <div>
          <dt>Layout</dt>
          <dd>{screen.layout}</dd>
        </div>
        <div>
          <dt>Display</dt>
          <dd>{screen.display_title}</dd>
        </div>
        <div>
          <dt>Icon</dt>
          <dd>{screen.display_icon}</dd>
        </div>
        <div>
          <dt>Offline</dt>
          <dd>{screen.offline_cache_strategy}</dd>
        </div>
        <div>
          <dt>Sync required</dt>
          <dd>{screen.sync_required ? "yes" : "no"}</dd>
        </div>
      </dl>
      <div className="app-component-stack">
        {screen.top_level_components.map((component) => (
          <ComponentBlock component={component} key={component.component_id} />
        ))}
      </div>
      <div className="screen-card-footer">
        <span className="queue-count">{screen.component_count} components</span>
        <span className="queue-count">{screen.action_count} actions</span>
      </div>
    </article>
  );
}

type ComponentBlockProps = {
  component: AppComponent;
};

function ComponentBlock({ component }: ComponentBlockProps) {
  return (
    <article className="canvas-field">
      <div>
        <strong>{component.label ?? component.component_id}</strong>
        <span>{component.binding?.form_id ?? component.binding?.data_path ?? component.binding?.action_id ?? "unbound"}</span>
      </div>
      <span className="status status-draft">{component.component_type}</span>
    </article>
  );
}

type ComponentPropertiesListProps = {
  items: AppComponentPropertySummary[];
};

function ComponentPropertiesList({ items }: ComponentPropertiesListProps) {
  return (
    <section className="field-properties-list" aria-label="Component properties">
      <h3>Component properties</h3>
      {items.length > 0 ? (
        items.map((item) => (
          <article className="field-properties" key={`${item.screen_id}-${item.component_id}`}>
            <p className="eyebrow">
              {item.screen_name} - {item.screen_id}
            </p>
            <h4>{item.label}</h4>
            <dl className="property-list">
              <div>
                <dt>Component</dt>
                <dd>{item.component_id}</dd>
              </div>
              <div>
                <dt>Type</dt>
                <dd>{item.component_type}</dd>
              </div>
              <div>
                <dt>Binding</dt>
                <dd>{item.binding}</dd>
              </div>
              <div>
                <dt>Children</dt>
                <dd>{item.child_count}</dd>
              </div>
              <div>
                <dt>Custom</dt>
                <dd>{formatComponentProperties(item)}</dd>
              </div>
            </dl>
          </article>
        ))
      ) : (
        <p>No component properties are configured.</p>
      )}
    </section>
  );
}

function formatComponentProperties(item: AppComponentPropertySummary): string {
  if (item.property_count === 0) {
    return "none";
  }

  return item.properties.map((property) => `${property.name}: ${property.value}`).join(", ");
}

type ActionPanelProps = {
  actions: AppActionSummary[];
};

function ActionPanel({ actions }: ActionPanelProps) {
  return (
    <section className="validation-panel" aria-label="Screen actions">
      <div className="preview-panel-heading">
        <h3>Actions</h3>
        <span className="queue-count">{actions.length} actions</span>
      </div>
      {actions.length > 0 ? (
        <div className="validation-rule-list">
          {actions.map((action) => (
            <article className="validation-rule action-binding-rule" key={`${action.screen_id}-${action.action_id}`}>
              <div>
                <p className="eyebrow">{action.screen_id}</p>
                <h4>{action.label}</h4>
              </div>
              <strong>{action.action_type}</strong>
              <dl className="action-binding-meta">
                <div>
                  <dt>Target</dt>
                  <dd>{action.target}</dd>
                </div>
                <div>
                  <dt>Binding</dt>
                  <dd>{action.binding}</dd>
                </div>
                <div>
                  <dt>Payload</dt>
                  <dd>{action.payload_path}</dd>
                </div>
                <div>
                  <dt>Result</dt>
                  <dd>{action.result_path}</dd>
                </div>
                <div>
                  <dt>Confirm</dt>
                  <dd>{action.confirm}</dd>
                </div>
                <div>
                  <dt>Success</dt>
                  <dd>{action.success}</dd>
                </div>
                <div>
                  <dt>Error</dt>
                  <dd>{action.error}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p>No screen actions are configured.</p>
      )}
    </section>
  );
}
