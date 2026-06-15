import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuthenticatedUser } from "../auth/AuthProvider";
import { canAccessModule } from "../auth/permissions";
import { findAdminModuleByRoute, getOrderedAdminModules } from "../modules/moduleRegistry";
import type { IconName } from "../design-system";
import { DashboardView } from "./views/DashboardView";
import { PlaceholderView } from "./views/PlaceholderView";
import { ThemeListView } from "./views/ThemeListView";
import { UnauthorizedView } from "./views/UnauthorizedView";

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
  const module = findAdminModuleByRoute(pathname);

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

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<GuardedRoute route={adminRoutes[0]} user={user} view={<DashboardView />} />} />
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

function getRouteView(route: AdminRoute): ReactNode {
  if (route.path === "/themes") {
    return <ThemeListView />;
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
