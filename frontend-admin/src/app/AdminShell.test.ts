import { describe, expect, it } from "vitest";

import { countQueueItemsByStatus, shellMetrics, workQueue } from "./adminShellModel";
import { adminRoutes, findAdminRoute } from "./routes";

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
    expect(findAdminRoute("/unknown")).toBeUndefined();
  });
});
