import { expect, test } from "@playwright/test";

test("signs in and renders the dashboard shell", async ({ page }) => {
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
});
