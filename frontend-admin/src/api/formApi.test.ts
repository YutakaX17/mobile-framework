import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import { countFormsByStatus, fetchFormSummaries, type FormSummary } from "./formApi";

const form: FormSummary = {
  current_revision: {
    field_count: 3,
    revision: 1,
    schema_version: "v1",
    status: "published",
    version: "0.1.0"
  },
  description: "Basic offline-capable intake form.",
  form_id: "patient_intake",
  mode: "standalone",
  name: "Patient Intake"
};

describe("form API helpers", () => {
  it("loads form summaries for a tenant", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ forms: [form] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const forms = await fetchFormSummaries(client, "demo");

    expect(requestedUrl).toBe("/api/forms/?tenant=demo");
    expect(forms).toEqual([form]);
  });

  it("rejects malformed form list responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ items: [] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchFormSummaries(client, "demo")).rejects.toThrow("forms array");
  });

  it("counts forms by current revision status", () => {
    expect(countFormsByStatus([form], "published")).toBe(1);
    expect(countFormsByStatus([form], "draft")).toBe(0);
  });
});
