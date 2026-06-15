import { NavLink } from "react-router-dom";

import { useAuthSession } from "../auth/AuthProvider";
import { AdminIcon } from "../design-system";
import { AdminRoutes, adminRoutes, useCurrentRoute } from "./routes";

export function AdminShell() {
  const currentRoute = useCurrentRoute();
  const { signOut, state } = useAuthSession();

  return (
    <main className="admin-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">
            MF
          </span>
          <span className="brand-name">Mobile Framework</span>
        </div>
        <nav className="nav-list">
          {adminRoutes.map((route) => (
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
          <div>
            <p className="eyebrow">{currentRoute?.section ?? "Unknown route"}</p>
            <h1>{currentRoute?.summary ?? "Workspace not found"}</h1>
          </div>
          <div className="topbar-actions" aria-label="Current workspace controls">
            <span className="user-chip">{state.user?.displayName}</span>
            <button type="button">
              <AdminIcon name="validate" />
              Validate
            </button>
            <button type="button" className="primary-action">
              <AdminIcon name="publish" />
              Publish review
            </button>
            <button type="button" onClick={signOut}>
              <AdminIcon name="signOut" />
              Sign out
            </button>
          </div>
        </header>

        <AdminRoutes />
      </section>
    </main>
  );
}
