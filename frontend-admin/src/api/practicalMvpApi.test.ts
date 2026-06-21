import { describe, expect, it, vi } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import {
  activateDeploymentPackage,
  activePackage,
  compileDeploymentPackage,
  fetchActiveManifest,
  fetchDeploymentPackages,
  fetchModuleStatuses,
  moduleCompatibilityCount,
  nextPatchVersion,
  packageIdFor
} from "./practicalMvpApi";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
  });
}

describe("practical MVP api", () => {
  it("loads module status for a tenant", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      jsonResponse({
        modules: [
          {
            compatibility: { is_compatible: true, message: "ok", platform_version: "0.1.0" },
            module_id: "field_ops",
            name: "Field Ops",
            plugin_api_version: 0,
            status: "enabled",
            version: "0.1.0"
          }
        ]
      })
    );
    const modules = await fetchModuleStatuses(createAdminApiClient({ fetcher }), "demo");

    expect(fetcher).toHaveBeenCalledWith("/api/modules/?tenant=demo", expect.objectContaining({ method: "GET" }));
    expect(moduleCompatibilityCount(modules)).toBe(1);
  });

  it("compiles and activates deployment packages", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          package: {
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
            status: "signed",
            updated_at: "2026-06-21T15:00:00Z"
          }
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          package: {
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
            status: "active",
            updated_at: "2026-06-21T15:01:00Z"
          }
        })
      );
    const client = createAdminApiClient({ fetcher });
    const compiled = await compileDeploymentPackage(
      {
        app_id: "field_ops_app",
        channel: "dev",
        form_ids: ["patient_intake"],
        package_id: "pkg_field_ops_app_0_1_1",
        theme_id: "field_ops"
      },
      client,
      "demo"
    );
    const activated = await activateDeploymentPackage(compiled.package_id, client, "demo");

    expect(compiled.status).toBe("signed");
    expect(activated.status).toBe("active");
    expect(fetcher).toHaveBeenNthCalledWith(
      1,
      "/api/deployment-packages/compile/?tenant=demo",
      expect.objectContaining({ method: "POST" })
    );
    expect(fetcher).toHaveBeenNthCalledWith(
      2,
      "/api/deployment-packages/pkg_field_ops_app_0_1_1/activate/?tenant=demo",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("loads package lists and tolerates a missing active manifest", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          packages: [
            {
              app_id: "field_ops_app",
              app_version: "0.1.0",
              channel: "dev",
              created_at: "2026-06-21T15:00:00Z",
              hash: "hash",
              package_id: "pkg_active",
              platform_version: "0.1.0",
              runtime_max_version: "0.1.0",
              runtime_min_version: "0.1.0",
              signature: "signature",
              status: "active",
              updated_at: "2026-06-21T15:00:00Z"
            }
          ]
        })
      )
      .mockResolvedValueOnce(jsonResponse({ error: { message: "missing" } }, 404));
    const client = createAdminApiClient({ fetcher });
    const packages = await fetchDeploymentPackages(client, "demo");
    const manifest = await fetchActiveManifest("field_ops_app", client, "demo");

    expect(activePackage(packages)?.package_id).toBe("pkg_active");
    expect(manifest).toBeUndefined();
  });

  it("formats versions and package ids", () => {
    expect(nextPatchVersion("0.1.9")).toBe("0.1.10");
    expect(nextPatchVersion("bad")).toBe("0.1.1");
    expect(packageIdFor("field_ops_app", "0.1.10")).toBe("pkg_field_ops_app_0_1_10");
  });
});
