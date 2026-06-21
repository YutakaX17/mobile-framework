import { expect, test } from "@playwright/test";

test("signs in and renders the dashboard shell", async ({ page }) => {
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
});
