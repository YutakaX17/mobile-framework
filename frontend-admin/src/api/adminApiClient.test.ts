import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  buildApiUrl,
  createAdminApiClient,
  resolveAdminApiBaseUrl
} from "./adminApiClient";

describe("admin api client", () => {
  it("resolves a default local API base URL", () => {
    expect(resolveAdminApiBaseUrl({})).toBe("/api");
    expect(resolveAdminApiBaseUrl({ VITE_ADMIN_API_BASE_URL: " https://example.test/api/ " })).toBe(
      "https://example.test/api"
    );
  });

  it("builds request URLs with normalized paths and query values", () => {
    expect(
      buildApiUrl("https://example.test/api/", "modules", {
        active: true,
        page: 2,
        skipped: undefined
      })
    ).toBe("https://example.test/api/modules?active=true&page=2");
  });

  it("sends JSON requests and parses JSON responses", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        headers: { "Content-Type": "application/json" },
        status: 201,
        statusText: "Created"
      })
    );
    const client = createAdminApiClient({
      baseUrl: "/admin-api",
      fetcher,
      headers: { "X-Client": "admin" }
    });

    const result = await client.post<{ ok: boolean }, { name: string }>("/modules", { name: "forms" });

    expect(result).toMatchObject({ data: { ok: true }, status: 201, url: "/admin-api/modules" });
    expect(fetcher).toHaveBeenCalledWith(
      "/admin-api/modules",
      expect.objectContaining({
        body: JSON.stringify({ name: "forms" }),
        method: "POST"
      })
    );
    const [, init] = fetcher.mock.calls[0];
    expect((init?.headers as Headers).get("Accept")).toBe("application/json");
    expect((init?.headers as Headers).get("Content-Type")).toBe("application/json");
    expect((init?.headers as Headers).get("X-Client")).toBe("admin");
  });

  it("throws typed errors for non-success responses", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ code: "validation_error" }), {
        headers: { "Content-Type": "application/json" },
        status: 422,
        statusText: "Unprocessable Entity"
      })
    );
    const client = createAdminApiClient({ baseUrl: "/api", fetcher });

    await expect(client.get("/forms")).rejects.toMatchObject({
      body: { code: "validation_error" },
      status: 422,
      statusText: "Unprocessable Entity"
    } satisfies Partial<ApiClientError>);
  });
});
