import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { findAdminModuleByRoute, getOrderedAdminModules } from "../modules/moduleRegistry";
import { DashboardView } from "./views/DashboardView";
import { PlaceholderView } from "./views/PlaceholderView";

export type AdminRoute = {
  path: string;
  label: string;
  section: string;
  summary: string;
};

export const adminRoutes: AdminRoute[] = getOrderedAdminModules().map((module) => ({
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
    path: module.routePath,
    section: module.section,
    summary: module.summary
  };
}

export function useCurrentRoute(): AdminRoute | undefined {
  return findAdminRoute(useLocation().pathname);
}

export function AdminRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardView />} />
      {adminRoutes
        .filter((route) => route.path !== "/dashboard")
        .map((route) => (
          <Route
            element={<PlaceholderView route={route} />}
            key={route.path}
            path={route.path}
          />
        ))}
      <Route path="*" element={<PlaceholderView route={undefined} />} />
    </Routes>
  );
}
