import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { AppRoutes } from "./app/AppRoutes";
import { ErrorBoundary } from "./app/ErrorBoundary";
import { NotificationProvider } from "./app/NotificationProvider";
import "./app/styles.css";
import { AuthProvider } from "./auth/AuthProvider";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element not found.");
}

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <ErrorBoundary>
        <NotificationProvider>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </NotificationProvider>
      </ErrorBoundary>
    </BrowserRouter>
  </StrictMode>,
);
