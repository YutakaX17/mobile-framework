import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuthSession } from "../auth/AuthProvider";
import { getLoginRedirectPath } from "../auth/authSession";
import { AdminShell } from "./AdminShell";
import { LoginView } from "./views/LoginView";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginView />} />
      <Route path="/*" element={<ProtectedAdminShell />} />
    </Routes>
  );
}

function ProtectedAdminShell() {
  const { state } = useAuthSession();
  const location = useLocation();

  if (state.status !== "authenticated") {
    return <Navigate to={getLoginRedirectPath(location.pathname, location.search)} replace />;
  }

  return <AdminShell />;
}
