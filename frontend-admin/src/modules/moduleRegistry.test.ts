import { describe, expect, it } from "vitest";

import {
  adminModuleContributions,
  findAdminModuleByRoute,
  getOrderedAdminModules,
  registerAdminModule,
  validateAdminModuleRegistry,
  type AdminModuleContribution
} from "./moduleRegistry";

describe("admin module registry", () => {
  it("keeps the initial admin modules in navigation order", () => {
    expect(getOrderedAdminModules().map((module) => module.routePath)).toEqual([
      "/dashboard",
      "/setup",
      "/apps",
      "/forms",
      "/themes",
      "/workflows",
      "/modules",
      "/deployments"
    ]);
  });

  it("finds module contributions by route", () => {
    expect(findAdminModuleByRoute("/themes")?.label).toBe("Themes");
    expect(findAdminModuleByRoute("/unknown")).toBeUndefined();
  });

  it("validates the initial registry", () => {
    expect(validateAdminModuleRegistry()).toEqual({
      duplicateIds: [],
      duplicateRoutePaths: [],
      isValid: true
    });
  });

  it("rejects duplicate ids and route paths when registering modules", () => {
    const duplicate: AdminModuleContribution = {
      ...adminModuleContributions[0],
      label: "Duplicate dashboard"
    };

    expect(() => registerAdminModule(adminModuleContributions, duplicate)).toThrow(
      "Admin module registry contains duplicate ids or route paths."
    );
  });

  it("registers new modules in sorted order", () => {
    const contribution: AdminModuleContribution = {
      area: "builder",
      capabilities: ["reports:manage"],
      icon: "apps",
      id: "reports",
      label: "Reports",
      order: 25,
      routePath: "/reports",
      section: "Report builder",
      summary: "Reporting workspace"
    };

    expect(registerAdminModule(adminModuleContributions, contribution).map((module) => module.id)).toEqual([
      "dashboard",
      "setup",
      "apps",
      "reports",
      "forms",
      "themes",
      "workflows",
      "modules",
      "deployments"
    ]);
  });
});
