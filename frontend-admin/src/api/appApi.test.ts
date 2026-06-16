import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import { countAppsByStatus, fetchAppSummaries, type AppSummary } from "./appApi";

const app: AppSummary = {
  app_id: "field_ops_app",
  current_revision: {
    navigation_count: 1,
    permission_count: 1,
    revision: 1,
    schema_version: "v1",
    screen_count: 1,
    status: "published",
    version: "0.1.0"
  },
  description: "Mobile field operations starter app.",
  name: "Field Operations"
};

describe("app API helpers", () => {
  it("loads app summaries for a tenant", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ apps: [app] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const apps = await fetchAppSummaries(client, "demo");

    expect(requestedUrl).toBe("/api/apps/?tenant=demo");
    expect(apps).toEqual([app]);
  });

  it("rejects malformed app list responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ items: [] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchAppSummaries(client, "demo")).rejects.toThrow("apps array");
  });

  it("counts apps by current revision status", () => {
    expect(countAppsByStatus([app], "published")).toBe(1);
    expect(countAppsByStatus([app], "draft")).toBe(0);
  });
});
