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
  group?: "primary" | "secondary" | "overflow";
  icon?: string;
  is_default?: boolean;
  label: string;
  order?: number;
  permission?: string;
  presentation?: "tab" | "drawer" | "hidden";
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
  permission?: string;
  properties?: Record<string, string | number | boolean | null>;
};

export type AppAction = {
  action_id: string;
  action_type: string;
  binding?: {
    component_id?: string;
    event: "load" | "tap" | "submit" | "change";
    payload_path?: string;
    result_path?: string;
    source: "screen" | "component" | "form" | "navigation";
  };
  confirm?: {
    message: string;
    title: string;
  };
  label?: string;
  on_error?: {
    message?: string;
    retry_allowed?: boolean;
  };
  on_success?: {
    message?: string;
    navigate_to?: string;
    refresh_screen?: boolean;
  };
  permission?: string;
  target?: string;
};

export type AppScreen = {
  actions?: AppAction[];
  components: AppComponent[];
  display?: {
    description?: string;
    icon?: string;
    title?: string;
  };
  layout?: {
    type?: string;
  };
  name: string;
  offline?: {
    cache_strategy?: "none" | "screen" | "screen_and_data";
    sync_required?: boolean;
  };
  order?: number;
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
  display_description: string;
  display_icon: string;
  display_title: string;
  layout: string;
  name: string;
  offline_cache_strategy: string;
  order: number;
  route: string;
  screen_id: string;
  screen_type: string;
  sync_required: boolean;
  top_level_components: AppComponent[];
};

export type AppActionSummary = {
  action_id: string;
  action_type: string;
  binding: string;
  confirm: string;
  error: string;
  label: string;
  payload_path: string;
  result_path: string;
  screen_id: string;
  success: string;
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

export type AppPermissionBindingSummary = {
  binding_type: "navigation" | "screen" | "action" | "component";
  label: string;
  permission: string;
  permission_label: string;
  screen_id: string;
  target_id: string;
};

export type AppMobilePreviewComponent = {
  binding: string;
  children: AppMobilePreviewComponent[];
  component_id: string;
  component_type: string;
  label: string;
};

export type AppMobilePreviewScreen = {
  actions: string[];
  components: AppMobilePreviewComponent[];
  navigation_label: string;
  route: string;
  screen_id: string;
  subtitle: string;
  title: string;
};

export type AppValidationFinding = {
  message: string;
  severity: "error" | "warning";
  target: string;
};

type AppListResponse = {
  apps: AppSummary[];
};

type AppDetailResponse = {
  app: AppDetail;
};

type AppUpdateResponse = {
  app: AppDetail;
  draft_revision: AppRevisionSummary;
};

type AppPublishResponse = {
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

export async function updateAppDraft(
  appId: string,
  payload: AppPayload,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<AppUpdateResponse> {
  const result = await client.put<AppUpdateResponse, AppPayload>(
    `/apps/${encodeURIComponent(appId)}/`,
    payload,
    { query: { tenant } }
  );

  if (!result.data || !isRecord(result.data.app) || !isRecord(result.data.draft_revision)) {
    throw new Error("App update response did not include app and draft revision objects.");
  }

  return result.data;
}

export async function publishAppRevision(
  appId: string,
  revision: number,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<AppDetail> {
  const result = await client.post<AppPublishResponse, Record<string, never>>(
    `/apps/${encodeURIComponent(appId)}/revisions/${revision}/publish/`,
    {},
    { query: { tenant } }
  );

  if (!result.data || !isRecord(result.data.app)) {
    throw new Error("App publish response did not include an app object.");
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
    display_description: screen.display?.description ?? "not set",
    display_icon: screen.display?.icon ?? "not set",
    display_title: screen.display?.title ?? screen.name,
    layout: screen.layout?.type ?? "single_column",
    name: screen.name,
    offline_cache_strategy: screen.offline?.cache_strategy ?? "none",
    order: screen.order ?? 0,
    route: screen.route ?? "not routed",
    screen_id: screen.screen_id,
    screen_type: screen.screen_type,
    sync_required: screen.offline?.sync_required ?? false,
    top_level_components: screen.components
  }));
}

export function getAppActionSummaries(payload: AppPayload | undefined): AppActionSummary[] {
  return (payload?.screens ?? []).flatMap((screen) =>
    (screen.actions ?? []).map((action) => ({
      action_id: action.action_id,
      action_type: action.action_type,
      binding: formatActionBinding(action),
      confirm: action.confirm?.title ?? "none",
      error: formatActionError(action),
      label: action.label ?? action.action_id,
      payload_path: action.binding?.payload_path ?? "not set",
      result_path: action.binding?.result_path ?? "not set",
      screen_id: screen.screen_id,
      success: formatActionSuccess(action),
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

export function getAppPermissionBindingSummaries(
  payload: AppPayload | undefined
): AppPermissionBindingSummary[] {
  const permissionLabels = new Map((payload?.permissions ?? []).map((permission) => [permission.code, permission.label]));
  const labelFor = (permission: string) => permissionLabels.get(permission) ?? "not declared";
  const navigationBindings = (payload?.navigation ?? [])
    .filter((item) => item.permission)
    .map((item) => ({
      binding_type: "navigation" as const,
      label: item.label,
      permission: item.permission ?? "",
      permission_label: labelFor(item.permission ?? ""),
      screen_id: item.screen_id,
      target_id: item.screen_id
    }));
  const screenBindings = (payload?.screens ?? []).flatMap((screen) => [
    ...(screen.permission
      ? [
          {
            binding_type: "screen" as const,
            label: screen.name,
            permission: screen.permission,
            permission_label: labelFor(screen.permission),
            screen_id: screen.screen_id,
            target_id: screen.screen_id
          }
        ]
      : []),
    ...(screen.actions ?? [])
      .filter((action) => action.permission)
      .map((action) => ({
        binding_type: "action" as const,
        label: action.label ?? action.action_id,
        permission: action.permission ?? "",
        permission_label: labelFor(action.permission ?? ""),
        screen_id: screen.screen_id,
        target_id: action.action_id
      })),
    ...screen.components.flatMap((component) => flattenComponentPermissionBindings(screen, component, labelFor))
  ]);

  return [...navigationBindings, ...screenBindings];
}

export function getAppMobilePreviewScreens(payload: AppPayload | undefined): AppMobilePreviewScreen[] {
  const navigationLabels = new Map((payload?.navigation ?? []).map((item) => [item.screen_id, item.label]));

  return (payload?.screens ?? []).map((screen) => ({
    actions: (screen.actions ?? []).map((action) => action.label ?? action.action_id),
    components: screen.components.map((component) => getMobilePreviewComponent(component)),
    navigation_label: navigationLabels.get(screen.screen_id) ?? "not in navigation",
    route: screen.route ?? "not routed",
    screen_id: screen.screen_id,
    subtitle: screen.display?.description ?? screen.screen_type,
    title: screen.display?.title ?? screen.name
  }));
}

export function getAppValidationFindings(payload: AppPayload | undefined): AppValidationFinding[] {
  if (!payload) {
    return [
      {
        message: "App payload is missing.",
        severity: "error",
        target: "payload"
      }
    ];
  }

  const findings: AppValidationFinding[] = [];
  const screens = payload.screens ?? [];
  const screenIds = new Set<string>();
  const duplicateScreenIds = new Set<string>();
  const permissions = new Set((payload.permissions ?? []).map((permission) => permission.code));

  for (const screen of screens) {
    if (screenIds.has(screen.screen_id)) {
      duplicateScreenIds.add(screen.screen_id);
    }
    screenIds.add(screen.screen_id);
  }

  for (const screenId of duplicateScreenIds) {
    findings.push({
      message: "Screen id is duplicated.",
      severity: "error",
      target: `screen:${screenId}`
    });
  }

  for (const item of payload.navigation) {
    if (!screenIds.has(item.screen_id)) {
      findings.push({
        message: "Navigation item points to a missing screen.",
        severity: "error",
        target: `navigation:${item.label}`
      });
    }
    pushPermissionFinding(findings, permissions, item.permission, `navigation:${item.label}`);
  }

  for (const screen of screens) {
    pushPermissionFinding(findings, permissions, screen.permission, `screen:${screen.screen_id}`);
    const componentIds = new Set(flattenComponents(screen.components).map((component) => component.component_id));
    const actionIds = new Set((screen.actions ?? []).map((action) => action.action_id));

    for (const component of flattenComponents(screen.components)) {
      pushPermissionFinding(findings, permissions, component.permission, `component:${component.component_id}`);
      if (component.binding?.action_id && !actionIds.has(component.binding.action_id)) {
        findings.push({
          message: "Component action binding points to a missing screen action.",
          severity: "error",
          target: `component:${component.component_id}`
        });
      }
    }

    for (const action of screen.actions ?? []) {
      pushPermissionFinding(findings, permissions, action.permission, `action:${action.action_id}`);
      if (action.binding?.component_id && !componentIds.has(action.binding.component_id)) {
        findings.push({
          message: "Action binding points to a missing component.",
          severity: "error",
          target: `action:${action.action_id}`
        });
      }
      if (action.action_type === "navigate" && action.target && !screenIds.has(action.target)) {
        findings.push({
          message: "Navigate action target does not match a screen id.",
          severity: "warning",
          target: `action:${action.action_id}`
        });
      }
    }
  }

  return findings;
}

function countComponents(components: AppComponent[]): number {
  return components.reduce((total, component) => total + 1 + countComponents(component.children ?? []), 0);
}

function flattenComponents(components: AppComponent[]): AppComponent[] {
  return components.flatMap((component) => [component, ...flattenComponents(component.children ?? [])]);
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

function flattenComponentPermissionBindings(
  screen: AppScreen,
  component: AppComponent,
  labelFor: (permission: string) => string
): AppPermissionBindingSummary[] {
  return [
    ...(component.permission
      ? [
          {
            binding_type: "component" as const,
            label: component.label ?? component.component_id,
            permission: component.permission,
            permission_label: labelFor(component.permission),
            screen_id: screen.screen_id,
            target_id: component.component_id
          }
        ]
      : []),
    ...(component.children ?? []).flatMap((child) => flattenComponentPermissionBindings(screen, child, labelFor))
  ];
}

function getMobilePreviewComponent(component: AppComponent): AppMobilePreviewComponent {
  return {
    binding: formatComponentBinding(component),
    children: (component.children ?? []).map((child) => getMobilePreviewComponent(child)),
    component_id: component.component_id,
    component_type: component.component_type,
    label: component.label ?? component.component_id
  };
}

function pushPermissionFinding(
  findings: AppValidationFinding[],
  permissions: Set<string>,
  permission: string | undefined,
  target: string
): void {
  if (permission && !permissions.has(permission)) {
    findings.push({
      message: "Permission is referenced but not declared.",
      severity: "warning",
      target
    });
  }
}

function formatActionBinding(action: AppAction): string {
  if (!action.binding) {
    return "unbound";
  }

  return `${action.binding.source}:${action.binding.event}`;
}

function formatActionSuccess(action: AppAction): string {
  if (!action.on_success) {
    return "none";
  }

  return action.on_success.message ?? action.on_success.navigate_to ?? "configured";
}

function formatActionError(action: AppAction): string {
  if (!action.on_error) {
    return "none";
  }

  return action.on_error.message ?? (action.on_error.retry_allowed ? "retry allowed" : "configured");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
