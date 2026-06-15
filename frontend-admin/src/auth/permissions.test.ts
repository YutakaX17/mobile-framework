import { describe, expect, it } from "vitest";

import { adminModuleContributions } from "../modules/moduleRegistry";
import { canAccessModule, getCapabilitiesForRoles, hasCapability } from "./permissions";
import type { AdminAuthUser } from "./authSession";

const builderUser: AdminAuthUser = {
  displayName: "Builder",
  email: "builder@example.test",
  roles: ["builder"]
};

const platformAdmin: AdminAuthUser = {
  displayName: "Admin",
  email: "admin@example.test",
  roles: ["platform-admin"]
};

describe("permissions", () => {
  it("expands role capabilities in stable order", () => {
    expect(getCapabilitiesForRoles(["operator", "builder"])).toEqual([
      "apps:manage",
      "dashboard:view",
      "deployments:manage",
      "forms:manage",
      "themes:manage",
      "workflows:manage"
    ]);
  });

  it("checks explicit capabilities and platform admin wildcard access", () => {
    expect(hasCapability(builderUser, "forms:manage")).toBe(true);
    expect(hasCapability(builderUser, "deployments:manage")).toBe(false);
    expect(hasCapability(platformAdmin, "deployments:manage")).toBe(true);
    expect(hasCapability(undefined, "dashboard:view")).toBe(false);
  });

  it("checks module contribution access", () => {
    const formsModule = adminModuleContributions.find((module) => module.id === "forms");
    const deploymentsModule = adminModuleContributions.find((module) => module.id === "deployments");

    expect(formsModule).toBeDefined();
    expect(deploymentsModule).toBeDefined();
    expect(formsModule && canAccessModule(builderUser, formsModule)).toBe(true);
    expect(deploymentsModule && canAccessModule(builderUser, deploymentsModule)).toBe(false);
  });
});
