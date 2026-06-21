import { expect, test } from "@playwright/test";

test("signs in, opens the setup wizard, and publishes a dev package", async ({ page }) => {
  const theme = {
    current_revision: {
      payload: {
        name: "Field Ops",
        schema_version: "v1",
        theme_id: "field_ops",
        tokens: { colors: { primary: "#1d6f68" } },
        version: "0.1.0"
      },
      revision: 1,
      schema_version: "v1",
      status: "published",
      version: "0.1.0"
    },
    description: "Field Ops theme",
    name: "Field Ops",
    theme_id: "field_ops"
  };
  const form = {
    current_revision: {
      field_count: 1,
      payload: {
        fields: [
          {
            binding: { data_path: "patient.name" },
            field_id: "patient_name",
            field_type: "text",
            label: "Patient name",
            required: true
          }
        ],
        form_id: "patient_intake",
        mode: "standalone",
        name: "Patient intake",
        schema_version: "v1",
        version: "0.1.0"
      },
      revision: 1,
      schema_version: "v1",
      status: "published",
      version: "0.1.0"
    },
    description: "Patient intake form",
    form_id: "patient_intake",
    mode: "standalone",
    name: "Patient intake"
  };
  const app = {
    app_id: "field_ops_app",
    current_revision: {
      navigation_count: 1,
      payload: {
        app_id: "field_ops_app",
        name: "Field Ops",
        navigation: [{ label: "Intake", screen_id: "intake" }],
        schema_version: "v1",
        screens: [
          {
            components: [{ binding: { form_id: "patient_intake" }, component_id: "form", component_type: "form" }],
            display: { title: "Patient intake" },
            name: "Intake",
            screen_id: "intake",
            screen_type: "form"
          }
        ],
        theme_id: "field_ops",
        version: "0.1.0"
      },
      permission_count: 0,
      revision: 1,
      schema_version: "v1",
      screen_count: 1,
      status: "published",
      version: "0.1.0"
    },
    description: "Field Ops app",
    name: "Field Ops"
  };
  const activePackage = {
    app_id: "field_ops_app",
    app_version: "0.1.1",
    channel: "dev",
    created_at: "2026-06-21T15:00:00Z",
    hash: "hash",
    package_id: "pkg_field_ops_app_0_1_1",
    platform_version: "0.1.0",
    runtime_max_version: "0.1.0",
    runtime_min_version: "0.1.0",
    signature: "signature",
    signature_status: "present",
    status: "active",
    updated_at: "2026-06-21T15:01:00Z"
  };

  await page.route("**/api/auth/session/", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      status: 401,
      body: JSON.stringify({
        error: {
          code: "authentication_required",
          details: [],
          message: "Authentication is required.",
          status_code: 401
        }
      })
    });
  });
  await page.route("**/api/auth/csrf/", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ csrf_token: "smoke-csrf" })
    });
  });
  await page.route("**/api/auth/login/", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        user: {
          display_name: "Demo Admin",
          email: "demo-admin@example.com",
          id: 1,
          is_staff: true,
          username: "demo-admin"
        }
      })
    });
  });
  await page.route("**/api/auth/tenants/", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
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
      })
    });
  });
  await page.route("**/api/modules/**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        modules: [
          {
            compatibility: { is_compatible: true, message: "Compatible", platform_version: "0.1.0" },
            module_id: "field_ops",
            name: "Field Ops",
            plugin_api_version: 0,
            runtime_max_version: "0.1.0",
            runtime_min_version: "0.1.0",
            status: "enabled",
            templates: { forms: [{}] },
            version: "0.1.0"
          }
        ]
      })
    });
  });
  await page.route("**/api/themes/field_ops/**", async (route) => {
    const method = route.request().method();
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(
        method === "PUT"
          ? { draft_revision: { ...theme.current_revision, revision: 2, status: "draft", version: "0.1.1" }, theme }
          : { theme: method === "POST" ? { ...theme, current_revision: { ...theme.current_revision, version: "0.1.1" } } : theme }
      )
    });
  });
  await page.route("**/api/forms/patient_intake/**", async (route) => {
    const method = route.request().method();
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(
        method === "PUT"
          ? { draft_revision: { ...form.current_revision, revision: 2, status: "draft", version: "0.1.1" }, form }
          : { form: method === "POST" ? { ...form, current_revision: { ...form.current_revision, version: "0.1.1" } } : form }
      )
    });
  });
  await page.route("**/api/apps/field_ops_app/**", async (route) => {
    const method = route.request().method();
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(
        method === "PUT"
          ? { app, draft_revision: { ...app.current_revision, revision: 2, status: "draft", version: "0.1.1" } }
          : { app: method === "POST" ? { ...app, current_revision: { ...app.current_revision, version: "0.1.1" } } : app }
      )
    });
  });
  await page.route("**/api/deployment-packages/compile/**", async (route) => {
    await route.fulfill({ contentType: "application/json", status: 201, body: JSON.stringify({ package: activePackage }) });
  });
  await page.route("**/api/deployment-packages/*/activate/**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ package: activePackage }) });
  });
  await page.route("**/api/deployment-packages/**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ packages: [activePackage] }) });
  });
  await page.route("**/api/mobile/packages/manifest/**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ manifest: activePackage }) });
  });

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Operational control surface" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Forms" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Validate" })).toBeVisible();

  await page.getByRole("link", { name: "Workflows" }).click();
  await expect(page.getByRole("heading", { name: "Patient intake approval" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Workflow canvas" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Workflow simulator" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "Task inbox" })).toBeVisible();

  await page.getByRole("link", { name: "Setup" }).click();
  await expect(page.getByRole("heading", { name: "Field Ops setup" })).toBeVisible();
  await expect(page.getByText("Field Ops 0.1.0")).toBeVisible();
  await page.getByRole("button", { name: "Publish dev package" }).click();
  await expect(page.getByText("pkg_field_ops_app_0_1_1 on dev")).toBeVisible();
});
