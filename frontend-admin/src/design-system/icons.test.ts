import { describe, expect, it } from "vitest";

import { getAdminIcon, listAdminIconNames } from "./icons";

describe("admin icon registry", () => {
  it("registers the shell and module icons", () => {
    expect(listAdminIconNames()).toEqual([
      "apps",
      "dashboard",
      "deployments",
      "forms",
      "login",
      "publish",
      "signOut",
      "themes",
      "validate",
      "workflows"
    ]);
  });

  it("returns icon components for registered names", () => {
    expect(getAdminIcon("dashboard")).toBeDefined();
    expect(getAdminIcon("publish")).toBeDefined();
  });
});
