import { describe, expect, it } from "vitest";

import type { ThemePayload } from "../api/themeApi";
import { contrastRatio, formatContrastRatio, getThemeContrastChecks, parseHexColor } from "./themeContrast";

const payload: ThemePayload = {
  modes: [
    {
      color_overrides: {
        background: "#FFFFFF",
        text: "#111827"
      },
      label: "Light",
      mode_id: "light"
    },
    {
      color_overrides: {
        background: "#777777",
        text: "#888888"
      },
      label: "Muted",
      mode_id: "muted"
    }
  ],
  name: "Field Operations",
  schema_version: "v1",
  theme_id: "field_ops",
  tokens: {
    colors: {
      background: "#FFFFFF",
      primary: {
        contrast: "#FFFFFF",
        main: "#0B5FFF"
      },
      weak: {
        contrast: "#777777",
        main: "#888888"
      }
    }
  },
  version: "0.1.0"
};

describe("theme contrast helpers", () => {
  it("parses six and eight digit hex colors", () => {
    expect(parseHexColor("#0B5FFF")).toEqual({ blue: 255, green: 95, red: 11 });
    expect(parseHexColor("#0B5FFFFF")).toEqual({ blue: 255, green: 95, red: 11 });
    expect(parseHexColor("not-a-color")).toBeUndefined();
  });

  it("calculates and formats contrast ratios", () => {
    expect(contrastRatio("#FFFFFF", "#000000")).toBeCloseTo(21, 2);
    expect(formatContrastRatio(4.567)).toBe("4.57:1");
    expect(contrastRatio("#FFFFFF", "bad")).toBeUndefined();
  });

  it("extracts contrast checks from theme scales and modes", () => {
    const checks = getThemeContrastChecks(payload);

    expect(checks.map((check) => check.label)).toEqual([
      "primary scale",
      "weak scale",
      "Light mode",
      "Muted mode"
    ]);
    expect(checks[0].passesAA).toBe(true);
    expect(checks[0].passesAAA).toBe(false);
    expect(checks[1].passesAA).toBe(false);
  });
});
