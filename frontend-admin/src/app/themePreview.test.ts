import { describe, expect, it } from "vitest";

import type { ThemePayload } from "../api/themeApi";
import { getThemePreviewModeOptions, resolveThemePreviewTokens } from "./themePreview";

const payload: ThemePayload = {
  modes: [
    {
      color_overrides: {
        background: "#111827",
        surface: "#1F2937",
        text: "#F9FAFB"
      },
      label: "Dark",
      mode_id: "dark"
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
      },
      surface: "#FFFFFF",
      text: "#172033"
    },
    radius: {
      md: 10
    },
    spacing: {
      md: 16
    },
    typography: {
      font_family: "Atkinson Hyperlegible"
    }
  },
  version: "0.1.0"
};

describe("theme preview helpers", () => {
  it("returns mode options from the theme payload", () => {
    expect(getThemePreviewModeOptions(payload)).toEqual([{ id: "dark", label: "Dark" }]);
  });

  it("resolves preview tokens from base theme tokens", () => {
    expect(resolveThemePreviewTokens(payload)).toEqual({
      background: "#F6F8FB",
      borderRadius: 10,
      buttonText: "#FFFFFF",
      fontFamily: "Atkinson Hyperlegible",
      padding: 16,
      primary: "#0B5FFF",
      surface: "#FFFFFF",
      text: "#172033"
    });
  });

  it("applies mode color overrides when selected", () => {
    const tokens = resolveThemePreviewTokens(payload, "dark");

    expect(tokens.background).toBe("#111827");
    expect(tokens.surface).toBe("#1F2937");
    expect(tokens.text).toBe("#F9FAFB");
    expect(tokens.primary).toBe("#0B5FFF");
  });

  it("falls back when payload tokens are unavailable", () => {
    expect(resolveThemePreviewTokens(undefined).borderRadius).toBe(8);
    expect(resolveThemePreviewTokens(undefined).fontFamily).toBe("Inter, sans-serif");
  });
});
