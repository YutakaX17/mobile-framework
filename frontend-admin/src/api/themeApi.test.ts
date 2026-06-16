import { describe, expect, it } from "vitest";

import { createAdminApiClient } from "./adminApiClient";
import {
  countThemesByStatus,
  fetchThemeDetail,
  fetchThemeSummaries,
  getAssetTokenRows,
  getColorTokenRows,
  getModeRows,
  getNumberTokenRows,
  getThemePayload,
  getTypographyTokenRows,
  updateThemeDraft,
  type ThemePayload,
  type ThemeSummary
} from "./themeApi";

const theme: ThemeSummary = {
  current_revision: {
    payload: {
      assets: {
        icon_asset_id: "field_ops_icon",
        logo_asset_id: "field_ops_logo"
      },
      modes: [
        {
          color_overrides: {
            background: "#F6F8FB",
            text: "#172033"
          },
          label: "Light",
          mode_id: "light"
        }
      ],
      name: "Field Operations",
      schema_version: "v1",
      theme_id: "field_ops",
      tokens: {
        colors: {
          background: "#F6F8FB",
          primary: {
            contrast: "#FFFFFF",
            main: "#0B5FFF"
          }
        },
        radius: {
          md: 10
        },
        spacing: {
          sm: 8
        },
        typography: {
          fallback_family: "sans-serif",
          font_family: "Atkinson Hyperlegible",
          scale: {
            body: {
              font_size: 16,
              font_weight: 400,
              line_height: 24
            }
          }
        }
      },
      version: "0.1.0"
    },
    revision: 1,
    schema_version: "v1",
    status: "published",
    version: "0.1.0"
  },
  description: "Accessible starter theme for mobile field work.",
  name: "Field Operations",
  theme_id: "field_ops"
};

describe("theme API helpers", () => {
  it("loads theme summaries for a tenant", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ themes: [theme] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const themes = await fetchThemeSummaries(client, "demo");

    expect(requestedUrl).toBe("/api/themes/?tenant=demo");
    expect(themes).toEqual([theme]);
  });

  it("rejects malformed theme list responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ items: [] }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchThemeSummaries(client, "demo")).rejects.toThrow("themes array");
  });

  it("loads a theme detail payload", async () => {
    let requestedUrl = "";
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input) => {
        requestedUrl = String(input);
        return new Response(JSON.stringify({ theme }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        });
      }
    });

    const detail = await fetchThemeDetail("field_ops", client, "demo");

    expect(requestedUrl).toBe("/api/themes/field_ops/?tenant=demo");
    expect(detail.current_revision?.payload).toBeDefined();
  });

  it("rejects malformed theme detail responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ item: theme }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(fetchThemeDetail("field_ops", client, "demo")).rejects.toThrow("theme object");
  });

  it("updates a theme draft revision for a tenant", async () => {
    let requestedUrl = "";
    let requestInit: RequestInit | undefined;
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async (input, init) => {
        requestedUrl = String(input);
        requestInit = init;
        return new Response(
          JSON.stringify({
            draft_revision: {
              payload: theme.current_revision?.payload,
              revision: 2,
              schema_version: "v1",
              status: "draft",
              version: "0.2.0"
            },
            theme
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 200
          }
        );
      }
    });

    const result = await updateThemeDraft(
      "field_ops",
      theme.current_revision?.payload as ThemePayload,
      client,
      "demo"
    );

    expect(requestedUrl).toBe("/api/themes/field_ops/?tenant=demo");
    expect(requestInit?.method).toBe("PUT");
    expect(JSON.parse(String(requestInit?.body))).toMatchObject({ theme_id: "field_ops" });
    expect(result.draft_revision).toMatchObject({ revision: 2, status: "draft" });
  });

  it("rejects malformed theme update responses", async () => {
    const client = createAdminApiClient({
      baseUrl: "/api",
      fetcher: async () =>
        new Response(JSON.stringify({ theme }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
    });

    await expect(
      updateThemeDraft(
        "field_ops",
        theme.current_revision?.payload as ThemePayload,
        client,
        "demo"
      )
    ).rejects.toThrow("draft revision");
  });

  it("counts themes by current revision status", () => {
    expect(countThemesByStatus([theme], "published")).toBe(1);
    expect(countThemesByStatus([theme], "draft")).toBe(0);
  });

  it("extracts token rows from a theme payload", () => {
    const payload = getThemePayload(theme);

    expect(getColorTokenRows(payload)).toEqual([
      { label: "background", value: "#F6F8FB" },
      { detail: "contrast #FFFFFF", label: "primary", value: "#0B5FFF" }
    ]);
    expect(getAssetTokenRows(payload)).toEqual([
      { label: "logo_asset_id", value: "field_ops_logo" },
      { label: "icon_asset_id", value: "field_ops_icon" }
    ]);
    expect(getNumberTokenRows(payload, "spacing")).toEqual([{ label: "sm", value: "8px" }]);
    expect(getNumberTokenRows(payload, "radius")).toEqual([{ label: "md", value: "10px" }]);
    expect(getTypographyTokenRows(payload)[0]).toEqual({
      detail: "fallback sans-serif",
      label: "font_family",
      value: "Atkinson Hyperlegible"
    });
    expect(getModeRows(payload)).toEqual([{ detail: "2 color overrides", label: "light", value: "Light" }]);
  });

  it("returns no asset rows when payload assets are absent", () => {
    expect(getAssetTokenRows(undefined)).toEqual([]);
    expect(
      getAssetTokenRows({
        name: "No Assets",
        schema_version: "v1",
        theme_id: "no_assets",
        version: "0.1.0"
      })
    ).toEqual([]);
  });
});
