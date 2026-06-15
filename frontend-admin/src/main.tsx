import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AdminShell } from "./app/AdminShell";
import "./app/styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element not found.");
}

createRoot(root).render(
  <StrictMode>
    <AdminShell />
  </StrictMode>,
);
