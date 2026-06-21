import { describe, expect, it, vi } from "vitest";

import { createAdminApiClient } from "../api/adminApiClient";
import { createAuthApi, frontendRolesFromAssignments } from "./authApi";

const backendUser = {
  display_name: "Demo Admin",
  email: "demo-admin@example.com",
  id: 1,
  is_staff: true,
  username: "demo-admin"
};

const tenantAssignments = {
  tenants: [
    {
      permissions: [
        "builder.theme.manage",
        "builder.form.manage",
        "builder.app.manage",
        "builder.package.publish"
      ],
      role: {
        name: "Administrator",
        slug: "admin"
      },
      tenant: {
        id: "tenant-id",
        name: "Demo Tenant",
        slug: "demo",
        status: "active"
      }
    }
  ]
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
  });
}

describe("auth api", () => {
  it("maps backend role assignments to frontend capabilities", () => {
    expect(frontendRolesFromAssignments(tenantAssignments.tenants)).toEqual([
      "builder",
      "operator",
      "platform-admin"
    ]);
  });

  it("logs in through csrf, session login, and tenant loading", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: "csrf-123" }))
      .mockResolvedValueOnce(jsonResponse({ user: backendUser }))
      .mockResolvedValueOnce(jsonResponse(tenantAssignments));
    const client = createAdminApiClient({ baseUrl: "/api", fetcher });
    const authApi = createAuthApi(client);

    const user = await authApi.login({ password: "demo-admin-password", username: "demo-admin" });

    expect(user).toMatchObject({
      displayName: "Demo Admin",
      email: "demo-admin@example.com",
      roles: ["builder", "operator", "platform-admin"],
      tenant: { slug: "demo" },
      username: "demo-admin"
    });
    expect(fetcher).toHaveBeenNthCalledWith(
      2,
      "/api/auth/login/",
      expect.objectContaining({
        body: JSON.stringify({ password: "demo-admin-password", username: "demo-admin" }),
        method: "POST"
      })
    );
    const [, loginInit] = fetcher.mock.calls[1];
    expect((loginInit?.headers as Headers).get("X-CSRFToken")).toBe("csrf-123");
  });

  it("loads the current session and tenants", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(jsonResponse({ user: backendUser }))
      .mockResolvedValueOnce(jsonResponse(tenantAssignments));
    const client = createAdminApiClient({ baseUrl: "/api", fetcher });
    const authApi = createAuthApi(client);

    const user = await authApi.currentSession();

    expect(user.tenant?.slug).toBe("demo");
    expect(fetcher).toHaveBeenNthCalledWith(1, "/api/auth/session/", expect.objectContaining({ method: "GET" }));
    expect(fetcher).toHaveBeenNthCalledWith(2, "/api/auth/tenants/", expect.objectContaining({ method: "GET" }));
  });
});
