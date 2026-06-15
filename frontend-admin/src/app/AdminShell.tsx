import { NavLink } from "react-router-dom";

import { useAuthSession } from "../auth/AuthProvider";
import { canAccessModule } from "../auth/permissions";
import { AdminIcon } from "../design-system";
import { findAdminModuleByRoute } from "../modules/moduleRegistry";
import { NotificationCenter, useNotifications } from "./NotificationProvider";
import { AdminRoutes, adminRoutes, useCurrentRoute } from "./routes";
import { getShellActionClassName, getUserRoleLabel, shellActions } from "./shellLayoutModel";

export function AdminShell() {
  const currentRoute = useCurrentRoute();
  const { signOut, state } = useAuthSession();
  const { addNotification } = useNotifications();
  const visibleRoutes = adminRoutes.filter((route) => {
    const module = findAdminModuleByRoute(route.path);
    return module ? canAccessModule(state.user, module) : false;
  });

  return (
    <main className="admin-shell">
      <a className="skip-link" href="#workspace-content">
        Skip to workspace
      </a>
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">
            MF
          </span>
          <span className="brand-name">Mobile Framework</span>
        </div>
        <nav className="nav-list">
          {visibleRoutes.map((route) => (
            <NavLink
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              key={route.path}
              to={route.path}
            >
              <AdminIcon name={route.icon} />
              {route.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-main">
            <p className="eyebrow">{currentRoute?.section ?? "Unknown route"}</p>
            <h1>{currentRoute?.summary ?? "Workspace not found"}</h1>
          </div>
          <div className="topbar-actions" aria-label="Current workspace controls">
            {shellActions.map((action) => (
              <button
                className={getShellActionClassName(action)}
                key={action.id}
                onClick={() => addNotification(action.notification)}
                type="button"
              >
                <AdminIcon name={action.icon} />
                {action.label}
              </button>
            ))}
            <details className="user-menu">
              <summary>
                <span className="user-chip">{state.user?.displayName}</span>
              </summary>
              <div className="user-menu-panel">
                <strong>{state.user?.email}</strong>
                <span>{getUserRoleLabel(state.user?.roles ?? [])}</span>
                <button type="button" onClick={signOut}>
                  <AdminIcon name="signOut" />
                  Sign out
                </button>
              </div>
            </details>
          </div>
        </header>

        <section className="workspace-content" id="workspace-content" tabIndex={-1}>
          <AdminRoutes />
        </section>
        <NotificationCenter />
      </section>
    </main>
  );
}
