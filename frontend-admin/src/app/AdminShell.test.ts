import { describe, expect, it } from "vitest";

import { countQueueItemsByStatus, shellMetrics, workQueue } from "./adminShellModel";
import { adminRoutes, findAdminRoute } from "./routes";
import { getShellActionClassName, getUserRoleLabel, shellActions } from "./shellLayoutModel";

describe("admin shell model", () => {
  it("starts with operational dashboard metrics", () => {
    expect(shellMetrics.map((metric) => metric.label)).toEqual([
      "Draft packages",
      "Validation errors",
      "Pending publishes",
      "Active modules"
    ]);
  });

  it("tracks the initial builder queue by status", () => {
    expect(workQueue).toHaveLength(3);
    expect(countQueueItemsByStatus("ready")).toBe(1);
    expect(countQueueItemsByStatus("draft")).toBe(1);
    expect(countQueueItemsByStatus("blocked")).toBe(1);
  });

  it("defines the initial admin route map", () => {
    expect(adminRoutes.map((route) => route.path)).toEqual([
      "/dashboard",
      "/apps",
      "/forms",
      "/themes",
      "/workflows",
      "/deployments"
    ]);
    expect(findAdminRoute("/forms")?.label).toBe("Forms");
    expect(findAdminRoute("/forms")?.capabilities).toEqual(["forms:manage"]);
    expect(findAdminRoute("/unknown")).toBeUndefined();
  });

  it("routes themes to a dedicated workspace", () => {
    expect(findAdminRoute("/themes")?.summary).toBe("Design token workspace");
    expect(findAdminRoute("/themes/field_ops")?.path).toBe("/themes");
  });

  it("routes forms to a dedicated workspace", () => {
    expect(findAdminRoute("/forms")?.summary).toBe("Form definition workspace");
  });

  it("defines shell actions and user menu labels", () => {
    expect(shellActions.map((action) => action.id)).toEqual(["validate", "publish-review"]);
    expect(shellActions.map((action) => action.notification.title)).toEqual([
      "Validation queued",
      "Publish review pending"
    ]);
    expect(getShellActionClassName(shellActions[1])).toBe("primary-action");
    expect(getUserRoleLabel(["platform-admin", "builder"])).toBe("platform-admin, builder");
    expect(getUserRoleLabel([])).toBe("No roles assigned");
  });
});
