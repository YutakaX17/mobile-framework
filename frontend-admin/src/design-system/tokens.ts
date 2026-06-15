export type DesignTokenGroup = Record<string, string>;

export type DesignTokens = {
  color: DesignTokenGroup;
  font: DesignTokenGroup;
  radius: DesignTokenGroup;
  shadow: DesignTokenGroup;
  spacing: DesignTokenGroup;
};

export const designTokens: DesignTokens = {
  color: {
    accent: "#1d6f68",
    background: "#eef2f0",
    border: "#cfdbd5",
    borderStrong: "#a9b7b0",
    critical: "#bc3d3d",
    criticalSurface: "#f7dddd",
    focus: "#1d6f68",
    good: "#2d7a46",
    goodSurface: "#dff0e5",
    mark: "#f0b44c",
    navigation: "#17211d",
    navigationActive: "#29423b",
    surface: "#ffffff",
    surfaceSubtle: "#f5f7f6",
    text: "#17211d",
    textInverted: "#ffffff",
    textMuted: "#51625b",
    warning: "#bc7a16",
    warningSurface: "#fff2d6"
  },
  font: {
    familyBase: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
    sizeCaption: "0.76rem",
    sizeHeading: "1.75rem",
    weightBold: "700",
    weightExtraBold: "800"
  },
  radius: {
    md: "8px",
    pill: "999px",
    sm: "6px"
  },
  shadow: {
    focus: "0 0 0 2px #1d6f68"
  },
  spacing: {
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "24px",
    "2xl": "28px"
  }
};

export function flattenDesignTokens(tokens: DesignTokens = designTokens): Record<string, string> {
  return Object.fromEntries(
    Object.entries(tokens).flatMap(([group, values]) =>
      Object.entries(values).map(([name, value]) => [`--mf-${group}-${toKebabCase(name)}`, value])
    )
  );
}

export function buildDesignTokenCssVariables(tokens: DesignTokens = designTokens): string {
  return Object.entries(flattenDesignTokens(tokens))
    .map(([name, value]) => `${name}: ${value};`)
    .join("\n");
}

function toKebabCase(value: string): string {
  return value.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
}
