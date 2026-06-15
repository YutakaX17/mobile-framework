import { describe, expect, it } from "vitest";

import { createTestModuleContribution, createTestNotification, createTestUser } from "./testFixtures";

describe("test fixtures", () => {
  it("creates overridable auth users", () => {
    expect(createTestUser({ roles: ["builder"] })).toMatchObject({
      email: "test-admin@example.test",
      roles: ["builder"]
    });
  });

  it("creates overridable module contributions", () => {
    expect(createTestModuleContribution({ id: "reports", routePath: "/reports" })).toMatchObject({
      capabilities: ["test:manage"],
      id: "reports",
      routePath: "/reports"
    });
  });

  it("creates overridable notifications", () => {
    expect(createTestNotification({ tone: "success" })).toEqual({
      message: "A test notification was created.",
      title: "Test notification",
      tone: "success"
    });
  });
});
