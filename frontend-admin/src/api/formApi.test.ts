import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import {
  countFormsByStatus,
  fetchFormDetail,
  fetchFormSummaries,
  getFormCanvasSections,
  getFormPayload,
  getFormToolboxItems,
  type FormSummary
} from "./formApi";

const form: FormSummary = {
  current_revision: {
    field_count: 3,
    payload: {
      fields: [
        {
          binding: { data_path: "patient.full_name", entity_type: "patient" },
          field_id: "full_name",
          field_type: "text",
          label: "Full name",
          required: true
        },
        {
          binding: { data_path: "patient.age", entity_type: "patient" },
          field_id: "age",
          field_type: "number",
          label: "Age"
        },
        {
          binding: { data_path: "patient.gender", entity_type: "patient" },
          field_id: "gender",
          field_type: "select",
          label: "Gender",
          options: [{ label: "Female", value: "female" }]
        }
      ],
      form_id: "patient_intake",
      layout: {
        sections: [
          {
            field_ids: ["full_name", "age", "gender"],
            label: "Identity",
            section_id: "identity"
          }
        ],
        type: "sectioned"
      },
      mode: "standalone",
      name: "Patient Intake",
      schema_version: "v1",
      version: "0.1.0"
    },
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

  it("loads form detail payloads for a tenant", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ form }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const detail = await fetchFormDetail("patient_intake", client, "demo");

    expect(requestedUrl).toBe("/api/forms/patient_intake/?tenant=demo");
    expect(detail.current_revision?.payload).toBeDefined();
  });

  it("rejects malformed form detail responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ item: form }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchFormDetail("patient_intake", client, "demo")).rejects.toThrow("form object");
  });

  it("counts forms by current revision status", () => {
    expect(countFormsByStatus([form], "published")).toBe(1);
    expect(countFormsByStatus([form], "draft")).toBe(0);
  });

  it("extracts toolbox items and canvas sections from form payloads", () => {
    const payload = getFormPayload(form);

    expect(getFormToolboxItems(payload)).toEqual([
      { count: 1, field_type: "number", label: "Number" },
      { count: 1, field_type: "select", label: "Select" },
      { count: 1, field_type: "text", label: "Text" }
    ]);
    expect(getFormCanvasSections(payload)).toEqual([
      {
        fields: payload?.fields,
        label: "Identity",
        section_id: "identity"
      }
    ]);
  });
});
