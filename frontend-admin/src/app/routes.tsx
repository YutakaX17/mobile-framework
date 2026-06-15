import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { DashboardView } from "./views/DashboardView";
import { PlaceholderView } from "./views/PlaceholderView";

export type AdminRoute = {
  path: string;
  label: string;
  section: string;
  summary: string;
};

export const adminRoutes: AdminRoute[] = [
  {
    path: "/dashboard",
    label: "Dashboard",
    section: "Admin dashboard",
    summary: "Operational control surface"
  },
  {
    path: "/apps",
    label: "Apps",
    section: "App builder",
    summary: "App composition workspace"
  },
  {
    path: "/forms",
    label: "Forms",
    section: "Form builder",
    summary: "Form definition workspace"
  },
  {
    path: "/themes",
    label: "Themes",
    section: "Theme builder",
    summary: "Design token workspace"
  },
  {
    path: "/workflows",
    label: "Workflows",
    section: "Workflow builder",
    summary: "Approval and automation workspace"
  },
  {
    path: "/deployments",
    label: "Deployments",
    section: "Deployment manager",
    summary: "Package release workspace"
  }
];

export function findAdminRoute(pathname: string): AdminRoute | undefined {
  return adminRoutes.find((route) => route.path === pathname);
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
