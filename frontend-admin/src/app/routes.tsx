import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuthenticatedUser } from "../auth/AuthProvider";
import { canAccessModule } from "../auth/permissions";
import { findAdminModuleByRoute, getOrderedAdminModules } from "../modules/moduleRegistry";
import type { IconName } from "../design-system";
import { AppDesignerView } from "./views/AppDesignerView";
import { AppListView } from "./views/AppListView";
import { DashboardView } from "./views/DashboardView";
import { FormDesignerView } from "./views/FormDesignerView";
import { FormListView } from "./views/FormListView";
import { PlaceholderView } from "./views/PlaceholderView";
import { ThemeDetailView } from "./views/ThemeDetailView";
import { ThemeListView } from "./views/ThemeListView";
import { UnauthorizedView } from "./views/UnauthorizedView";
import { WorkflowEditorView } from "./views/WorkflowEditorView";

export type AdminRoute = {
  path: string;
  label: string;
  icon: IconName;
  capabilities: string[];
  section: string;
  summary: string;
};

export const adminRoutes: AdminRoute[] = getOrderedAdminModules().map((module) => ({
  icon: module.icon,
  capabilities: module.capabilities,
  label: module.label,
  path: module.routePath,
  section: module.section,
  summary: module.summary
}));

export function findAdminRoute(pathname: string): AdminRoute | undefined {
  const module = findAdminModuleByRoute(pathname) ?? findNestedAdminModule(pathname);

  if (!module) {
    return undefined;
  }

  return {
    label: module.label,
    icon: module.icon,
    capabilities: module.capabilities,
    path: module.routePath,
    section: module.section,
    summary: module.summary
  };
}

export function useCurrentRoute(): AdminRoute | undefined {
  return findAdminRoute(useLocation().pathname);
}

export function AdminRoutes() {
  const user = useAuthenticatedUser();
  const appsRoute = findAdminRoute("/apps");
  const formsRoute = findAdminRoute("/forms");
  const themesRoute = findAdminRoute("/themes");

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<GuardedRoute route={adminRoutes[0]} user={user} view={<DashboardView />} />} />
      {appsRoute ? (
        <Route
          path="/apps/:appId"
          element={<GuardedRoute route={appsRoute} user={user} view={<AppDesignerView />} />}
        />
      ) : null}
      {formsRoute ? (
        <Route
          path="/forms/:formId"
          element={<GuardedRoute route={formsRoute} user={user} view={<FormDesignerView />} />}
        />
      ) : null}
      {themesRoute ? (
        <Route
          path="/themes/:themeId"
          element={<GuardedRoute route={themesRoute} user={user} view={<ThemeDetailView />} />}
        />
      ) : null}
      {adminRoutes
        .filter((route) => route.path !== "/dashboard")
        .map((route) => (
          <Route
            element={<GuardedRoute route={route} user={user} view={getRouteView(route)} />}
            key={route.path}
            path={route.path}
          />
        ))}
      <Route path="*" element={<PlaceholderView route={undefined} />} />
    </Routes>
  );
}

function findNestedAdminModule(pathname: string) {
  if (pathname.startsWith("/apps/")) {
    return findAdminModuleByRoute("/apps");
  }

  if (pathname.startsWith("/forms/")) {
    return findAdminModuleByRoute("/forms");
  }

  if (pathname.startsWith("/themes/")) {
    return findAdminModuleByRoute("/themes");
  }

  return undefined;
}

function getRouteView(route: AdminRoute): ReactNode {
  if (route.path === "/apps") {
    return <AppListView />;
  }

  if (route.path === "/forms") {
    return <FormListView />;
  }

  if (route.path === "/themes") {
    return <ThemeListView />;
  }

  if (route.path === "/workflows") {
    return <WorkflowEditorView />;
  }

  return <PlaceholderView route={route} />;
}

type GuardedRouteProps = {
  route: AdminRoute;
  user: ReturnType<typeof useAuthenticatedUser>;
  view: ReactNode;
};

function GuardedRoute({ route, user, view }: GuardedRouteProps) {
  const module = findAdminModuleByRoute(route.path);

  if (!module || !canAccessModule(user, module)) {
    return <UnauthorizedView route={route} />;
  }

  return view;
}
