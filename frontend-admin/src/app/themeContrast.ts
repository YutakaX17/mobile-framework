import type { ThemeColorScale, ThemePayload } from "../api/themeApi";

export type RgbColor = {
  blue: number;
  green: number;
  red: number;
};

export type ContrastCheck = {
  background: string;
  foreground: string;
  label: string;
  passesAA: boolean;
  passesAAA: boolean;
  ratio: number;
};

export function parseHexColor(value: string): RgbColor | undefined {
  const normalized = value.trim().replace(/^#/, "");
  if (!/^[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(normalized)) {
    return undefined;
  }

  return {
    blue: Number.parseInt(normalized.slice(4, 6), 16),
    green: Number.parseInt(normalized.slice(2, 4), 16),
    red: Number.parseInt(normalized.slice(0, 2), 16)
  };
}

export function contrastRatio(foreground: string, background: string): number | undefined {
  const foregroundColor = parseHexColor(foreground);
  const backgroundColor = parseHexColor(background);
  if (!foregroundColor || !backgroundColor) {
    return undefined;
  }

  const foregroundLuminance = relativeLuminance(foregroundColor);
  const backgroundLuminance = relativeLuminance(backgroundColor);
  const lighter = Math.max(foregroundLuminance, backgroundLuminance);
  const darker = Math.min(foregroundLuminance, backgroundLuminance);

  return (lighter + 0.05) / (darker + 0.05);
}

export function formatContrastRatio(ratio: number): string {
  return `${ratio.toFixed(2)}:1`;
}

export function getThemeContrastChecks(payload: ThemePayload | undefined): ContrastCheck[] {
  if (!payload) {
    return [];
  }

  const checks: ContrastCheck[] = [];

  for (const [label, token] of Object.entries(payload.tokens?.colors ?? {})) {
    if (isColorScale(token) && token.main && token.contrast) {
      addContrastCheck(checks, `${label} scale`, token.contrast, token.main);
    }
  }

  for (const mode of payload.modes ?? []) {
    const foreground = mode.color_overrides.text;
    const background = mode.color_overrides.background;
    if (foreground && background) {
      addContrastCheck(checks, `${mode.label} mode`, foreground, background);
    }
  }

  return checks;
}

function addContrastCheck(checks: ContrastCheck[], label: string, foreground: string, background: string) {
  const ratio = contrastRatio(foreground, background);
  if (ratio === undefined) {
    return;
  }

  checks.push({
    background,
    foreground,
    label,
    passesAA: ratio >= 4.5,
    passesAAA: ratio >= 7,
    ratio
  });
}

function relativeLuminance(color: RgbColor): number {
  const channels = [color.red, color.green, color.blue].map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : Math.pow((normalized + 0.055) / 1.055, 2.4);
  });

  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

function isColorScale(value: unknown): value is ThemeColorScale {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
