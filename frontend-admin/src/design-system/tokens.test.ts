import { describe, expect, it } from "vitest";

import { buildDesignTokenCssVariables, designTokens, flattenDesignTokens } from "./tokens";

describe("design tokens", () => {
  it("defines the required token groups", () => {
    expect(Object.keys(designTokens)).toEqual(["color", "font", "radius", "shadow", "spacing"]);
  });

  it("flattens tokens into stable CSS custom properties", () => {
    expect(flattenDesignTokens()).toMatchObject({
      "--mf-color-accent": "#1d6f68",
      "--mf-color-background": "#eef2f0",
      "--mf-font-family-base":
        "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--mf-radius-md": "8px",
      "--mf-spacing-xl": "24px"
    });
  });

  it("does not emit duplicate custom property names", () => {
    const names = Object.keys(flattenDesignTokens());
    expect(new Set(names).size).toBe(names.length);
  });

  it("builds a CSS variable block for documentation and future generation", () => {
    const cssVariables = buildDesignTokenCssVariables();

    expect(cssVariables).toContain("--mf-color-text: #17211d;");
    expect(cssVariables).toContain("--mf-radius-pill: 999px;");
  });
});
