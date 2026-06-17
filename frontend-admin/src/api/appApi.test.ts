import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import {
  countAppsByStatus,
  fetchAppDetail,
  fetchAppSummaries,
  getAppActionSummaries,
  getAppCanvasScreens,
  getAppComponentPropertySummaries,
  getAppPayload,
  getAppPermissionBindingSummaries,
  type AppSummary
} from "./appApi";

const app: AppSummary = {
  app_id: "field_ops_app",
  current_revision: {
    payload: {
      app_id: "field_ops_app",
      name: "Field Operations",
      navigation: [
        {
          icon: "form",
          group: "primary",
          is_default: true,
          label: "Intake",
          order: 0,
          permission: "forms.submit_patient_intake",
          presentation: "tab",
          screen_id: "intake"
        }
      ],
      permissions: [
        {
          code: "forms.submit_patient_intake",
          label: "Submit patient intake"
        }
      ],
      schema_version: "v1",
      screens: [
        {
          actions: [
            {
              action_id: "submit_intake",
              action_type: "submit_form",
              binding: {
                component_id: "intake_form",
                event: "submit",
                payload_path: "forms.patient_intake",
                result_path: "submissions.patient_intake",
                source: "component"
              },
              confirm: {
                message: "Submit this patient intake form?",
                title: "Submit intake"
              },
              label: "Submit",
              on_error: {
                message: "Patient intake could not be submitted.",
                retry_allowed: true
              },
              on_success: {
                message: "Patient intake submitted.",
                refresh_screen: true
              },
              permission: "forms.submit_patient_intake",
              target: "patient_intake"
            }
          ],
          components: [
            {
              binding: {
                form_id: "patient_intake"
              },
              component_id: "intake_form",
              component_type: "form",
              label: "Patient Intake",
              permission: "forms.submit_patient_intake"
            }
          ],
          display: {
            description: "Capture a patient intake form.",
            icon: "form",
            title: "Patient Intake"
          },
          layout: {
            type: "single_column"
          },
          name: "Patient Intake",
          offline: {
            cache_strategy: "screen_and_data",
            sync_required: true
          },
          order: 0,
          permission: "forms.submit_patient_intake",
          route: "/intake",
          screen_id: "intake",
          screen_type: "form"
        }
      ],
      version: "0.1.0"
    },
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

  it("loads an app detail payload", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ app }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const detail = await fetchAppDetail("field_ops_app", client, "demo");

    expect(requestedUrl).toBe("/api/apps/field_ops_app/?tenant=demo");
    expect(detail.current_revision?.payload).toBeDefined();
  });

  it("rejects malformed app detail responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ item: app }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchAppDetail("field_ops_app", client, "demo")).rejects.toThrow("app object");
  });

  it("counts apps by current revision status", () => {
    expect(countAppsByStatus([app], "published")).toBe(1);
    expect(countAppsByStatus([app], "draft")).toBe(0);
  });

  it("extracts screen canvas summaries from an app payload", () => {
    const payload = getAppPayload(app);

    expect(getAppCanvasScreens(payload)).toEqual([
      {
        action_count: 1,
        component_count: 1,
        display_description: "Capture a patient intake form.",
        display_icon: "form",
        display_title: "Patient Intake",
        layout: "single_column",
        name: "Patient Intake",
        offline_cache_strategy: "screen_and_data",
        order: 0,
        route: "/intake",
        screen_id: "intake",
        screen_type: "form",
        sync_required: true,
        top_level_components: [
          {
            binding: {
              form_id: "patient_intake"
            },
            component_id: "intake_form",
            component_type: "form",
            label: "Patient Intake",
            permission: "forms.submit_patient_intake"
          }
        ]
      }
    ]);
    expect(getAppActionSummaries(payload)).toEqual([
      {
        action_id: "submit_intake",
        action_type: "submit_form",
        binding: "component:submit",
        confirm: "Submit intake",
        error: "Patient intake could not be submitted.",
        label: "Submit",
        payload_path: "forms.patient_intake",
        result_path: "submissions.patient_intake",
        screen_id: "intake",
        success: "Patient intake submitted.",
        target: "patient_intake"
      }
    ]);
  });

  it("extracts permission binding summaries from an app payload", () => {
    const payload = getAppPayload(app);

    expect(getAppPermissionBindingSummaries(payload)).toEqual([
      {
        binding_type: "navigation",
        label: "Intake",
        permission: "forms.submit_patient_intake",
        permission_label: "Submit patient intake",
        screen_id: "intake",
        target_id: "intake"
      },
      {
        binding_type: "screen",
        label: "Patient Intake",
        permission: "forms.submit_patient_intake",
        permission_label: "Submit patient intake",
        screen_id: "intake",
        target_id: "intake"
      },
      {
        binding_type: "action",
        label: "Submit",
        permission: "forms.submit_patient_intake",
        permission_label: "Submit patient intake",
        screen_id: "intake",
        target_id: "submit_intake"
      },
      {
        binding_type: "component",
        label: "Patient Intake",
        permission: "forms.submit_patient_intake",
        permission_label: "Submit patient intake",
        screen_id: "intake",
        target_id: "intake_form"
      }
    ]);
  });

  it("extracts component property summaries from an app payload", () => {
    const payload = getAppPayload(app);
    if (!payload) {
      throw new Error("Expected test payload to be available.");
    }
    const component = payload.screens[0].components[0];
    const enrichedPayload = {
      ...payload,
      screens: [
        {
          ...payload.screens[0],
          components: [
            {
              ...component,
              children: [
                {
                  binding: {
                    data_path: "patient.notes"
                  },
                  component_id: "notes",
                  component_type: "textarea",
                  properties: {
                    placeholder: "Optional notes",
                    rows: 3
                  }
                }
              ],
              properties: {
                disabled: false,
                submit_label: "Save"
              }
            }
          ]
        }
      ]
    };

    expect(getAppComponentPropertySummaries(enrichedPayload)).toEqual([
      {
        binding: "patient_intake",
        child_count: 1,
        component_id: "intake_form",
        component_type: "form",
        label: "Patient Intake",
        properties: [
          {
            name: "disabled",
            value: "false"
          },
          {
            name: "submit_label",
            value: "Save"
          }
        ],
        property_count: 2,
        screen_id: "intake",
        screen_name: "Patient Intake"
      },
      {
        binding: "patient.notes",
        child_count: 0,
        component_id: "notes",
        component_type: "textarea",
        label: "not set",
        properties: [
          {
            name: "placeholder",
            value: "Optional notes"
          },
          {
            name: "rows",
            value: "3"
          }
        ],
        property_count: 2,
        screen_id: "intake",
        screen_name: "Patient Intake"
      }
    ]);
  });
});
