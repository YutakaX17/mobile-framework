import { describe, expect, it } from "vitest";

import { countQueueItemsByStatus, shellMetrics, workQueue } from "./adminShellModel";

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
});
