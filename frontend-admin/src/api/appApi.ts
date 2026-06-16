import { adminApiClient, type AdminApiClient } from "./adminApiClient";

export type AppRevisionStatus = "draft" | "reviewed" | "published" | "archived";

export type AppRevisionSummary = {
  navigation_count: number;
  payload?: unknown;
  permission_count: number;
  revision: number;
  schema_version: string;
  screen_count: number;
  status: AppRevisionStatus;
  version: string;
};

export type AppSummary = {
  app_id: string;
  current_revision: AppRevisionSummary | null;
  description: string;
  name: string;
};

export type AppNavigationItem = {
  icon?: string;
  label: string;
  permission?: string;
  screen_id: string;
};

export type AppComponent = {
  binding?: {
    action_id?: string;
    data_path?: string;
    form_id?: string;
  };
  children?: AppComponent[];
  component_id: string;
  component_type: string;
  label?: string;
  properties?: Record<string, string | number | boolean | null>;
};

export type AppAction = {
  action_id: string;
  action_type: string;
  label?: string;
  permission?: string;
  target?: string;
};

export type AppScreen = {
  actions?: AppAction[];
  components: AppComponent[];
  layout?: {
    type?: string;
  };
  name: string;
  permission?: string;
  route?: string;
  screen_id: string;
  screen_type: string;
};

export type AppPayload = {
  app_id: string;
  description?: string;
  name: string;
  navigation: AppNavigationItem[];
  permissions?: { code: string; label: string }[];
  schema_version: string;
  screens: AppScreen[];
  theme_id?: string;
  version: string;
};

export type AppDetail = AppSummary;

export type AppCanvasScreen = {
  action_count: number;
  component_count: number;
  layout: string;
  name: string;
  route: string;
  screen_id: string;
  screen_type: string;
  top_level_components: AppComponent[];
};

export type AppActionSummary = {
  action_id: string;
  action_type: string;
  label: string;
  screen_id: string;
  target: string;
};

export type AppComponentPropertyRow = {
  name: string;
  value: string;
};

export type AppComponentPropertySummary = {
  binding: string;
  child_count: number;
  component_id: string;
  component_type: string;
  label: string;
  properties: AppComponentPropertyRow[];
  property_count: number;
  screen_id: string;
  screen_name: string;
};

type AppListResponse = {
  apps: AppSummary[];
};

type AppDetailResponse = {
  app: AppDetail;
};

export async function fetchAppSummaries(
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<AppSummary[]> {
  const result = await client.get<AppListResponse>("/apps/", { query: { tenant } });

  if (!result.data || !Array.isArray(result.data.apps)) {
    throw new Error("App list response did not include an apps array.");
  }

  return result.data.apps;
}

export async function fetchAppDetail(
  appId: string,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<AppDetail> {
  const result = await client.get<AppDetailResponse>(`/apps/${encodeURIComponent(appId)}/`, {
    query: { tenant }
  });

  if (!result.data || !isRecord(result.data.app)) {
    throw new Error("App detail response did not include an app object.");
  }

  return result.data.app;
}

export function countAppsByStatus(apps: AppSummary[], status: AppRevisionStatus): number {
  return apps.filter((app) => app.current_revision?.status === status).length;
}

export function getAppPayload(app: AppDetail): AppPayload | undefined {
  const payload = app.current_revision?.payload;
  if (!isRecord(payload) || !Array.isArray(payload.screens) || !Array.isArray(payload.navigation)) {
    return undefined;
  }

  return payload as AppPayload;
}

export function getAppCanvasScreens(payload: AppPayload | undefined): AppCanvasScreen[] {
  return (payload?.screens ?? []).map((screen) => ({
    action_count: screen.actions?.length ?? 0,
    component_count: countComponents(screen.components),
    layout: screen.layout?.type ?? "single_column",
    name: screen.name,
    route: screen.route ?? "not routed",
    screen_id: screen.screen_id,
    screen_type: screen.screen_type,
    top_level_components: screen.components
  }));
}

export function getAppActionSummaries(payload: AppPayload | undefined): AppActionSummary[] {
  return (payload?.screens ?? []).flatMap((screen) =>
    (screen.actions ?? []).map((action) => ({
      action_id: action.action_id,
      action_type: action.action_type,
      label: action.label ?? action.action_id,
      screen_id: screen.screen_id,
      target: action.target ?? "not set"
    }))
  );
}

export function getAppComponentPropertySummaries(
  payload: AppPayload | undefined
): AppComponentPropertySummary[] {
  return (payload?.screens ?? []).flatMap((screen) =>
    screen.components.flatMap((component) => flattenComponentProperties(screen, component))
  );
}

function countComponents(components: AppComponent[]): number {
  return components.reduce((total, component) => total + 1 + countComponents(component.children ?? []), 0);
}

function flattenComponentProperties(
  screen: AppScreen,
  component: AppComponent
): AppComponentPropertySummary[] {
  const properties = Object.entries(component.properties ?? {})
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, value]) => ({
      name,
      value: formatPropertyValue(value)
    }));

  return [
    {
      binding: formatComponentBinding(component),
      child_count: component.children?.length ?? 0,
      component_id: component.component_id,
      component_type: component.component_type,
      label: component.label ?? "not set",
      properties,
      property_count: properties.length,
      screen_id: screen.screen_id,
      screen_name: screen.name
    },
    ...(component.children ?? []).flatMap((child) => flattenComponentProperties(screen, child))
  ];
}

function formatComponentBinding(component: AppComponent): string {
  return component.binding?.form_id ?? component.binding?.data_path ?? component.binding?.action_id ?? "unbound";
}

function formatPropertyValue(value: string | number | boolean | null): string {
  if (value === null) {
    return "not set";
  }

  return String(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
