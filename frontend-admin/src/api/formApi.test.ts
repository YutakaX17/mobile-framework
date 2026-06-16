import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import {
  countFormsByStatus,
  fetchFormDetail,
  fetchFormSummaries,
  getFormCanvasSections,
  getFormFieldPropertySummaries,
  getFormLogicRuleSummaries,
  getFormPayload,
  getFormPropertyRows,
  getFormToolboxItems,
  getFormValidationRuleSummaries,
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
          required: true,
          validation: {
            max_length: 120,
            min_length: 2
          }
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

  it("extracts form and field property rows from form payloads", () => {
    const payload = getFormPayload(form);

    expect(getFormPropertyRows(payload)).toEqual([
      { label: "Form id", value: "patient_intake" },
      { label: "Version", value: "0.1.0" },
      { label: "Mode", value: "standalone" },
      { label: "Entity", value: "not set" },
      { label: "Layout", value: "sectioned" },
      { label: "Fields", value: "3" }
    ]);
    expect(getFormFieldPropertySummaries(payload)[0]).toEqual({
      field_id: "full_name",
      label: "Full name",
      rows: [
        { label: "Type", value: "Text" },
        { label: "Binding", value: "patient.full_name" },
        { label: "Required", value: "yes" },
        { label: "Read only", value: "no" },
        { label: "Options", value: "0" },
        { label: "Validation", value: "2" }
      ]
    });
  });

  it("extracts conditional logic rules from form payload fields", () => {
    const payload = getFormPayload(form);
    const payloadWithLogic = payload
      ? {
          ...payload,
          fields: [
            {
              ...payload.fields[0],
              visibility: {
                expression: "patient.age >= 18",
                rule_type: "supported_expression"
              }
            },
            {
              ...payload.fields[1],
              calculation: {
                expression: "current_year - patient.birth_year",
                rule_type: "server_evaluated"
              }
            }
          ]
        }
      : undefined;

    expect(getFormLogicRuleSummaries(payload)).toEqual([]);
    expect(getFormLogicRuleSummaries(payloadWithLogic)).toEqual([
      {
        expression: "patient.age >= 18",
        field_id: "full_name",
        field_label: "Full name",
        kind: "visibility",
        rule_type: "supported_expression"
      },
      {
        expression: "current_year - patient.birth_year",
        field_id: "age",
        field_label: "Age",
        kind: "calculation",
        rule_type: "server_evaluated"
      }
    ]);
  });

  it("extracts validation rule summaries from form payload fields", () => {
    const payload = getFormPayload(form);
    const payloadWithoutValidation = payload
      ? {
          ...payload,
          fields: payload.fields.map((field) => ({ ...field, validation: undefined }))
        }
      : undefined;

    expect(getFormValidationRuleSummaries(payloadWithoutValidation)).toEqual([]);
    expect(getFormValidationRuleSummaries(payload)).toEqual([
      {
        field_id: "full_name",
        field_label: "Full name",
        rule: "Max Length",
        value: "120"
      },
      {
        field_id: "full_name",
        field_label: "Full name",
        rule: "Min Length",
        value: "2"
      }
    ]);
  });
});
