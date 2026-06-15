import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import { countThemesByStatus, fetchThemeSummaries, type ThemeSummary } from "./themeApi";

const theme: ThemeSummary = {
  current_revision: {
    revision: 1,
    schema_version: "v1",
    status: "published",
    version: "0.1.0"
  },
  description: "Accessible starter theme for mobile field work.",
  name: "Field Operations",
  theme_id: "field_ops"
};

describe("theme API helpers", () => {
  it("loads theme summaries for a tenant", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ themes: [theme] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const themes = await fetchThemeSummaries(client, "demo");

    expect(requestedUrl).toBe("/api/themes/?tenant=demo");
    expect(themes).toEqual([theme]);
  });

  it("rejects malformed theme list responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ items: [] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchThemeSummaries(client, "demo")).rejects.toThrow("themes array");
  });

  it("counts themes by current revision status", () => {
    expect(countThemesByStatus([theme], "published")).toBe(1);
    expect(countThemesByStatus([theme], "draft")).toBe(0);
  });
});
