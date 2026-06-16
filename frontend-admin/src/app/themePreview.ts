import type { ThemeColorScale, ThemeMode, ThemePayload } from "../api/themeApi";

export type ThemePreviewModeOption = {
  id: string;
  label: string;
};

export type ThemePreviewTokens = {
  background: string;
  borderRadius: number;
  buttonText: string;
  fontFamily: string;
  padding: number;
  primary: string;
  surface: string;
  text: string;
};

export function getThemePreviewModeOptions(payload: ThemePayload | undefined): ThemePreviewModeOption[] {
  return (payload?.modes ?? []).map((mode) => ({
    id: mode.mode_id,
    label: mode.label
  }));
}

export function resolveThemePreviewTokens(
  payload: ThemePayload | undefined,
  modeId?: string
): ThemePreviewTokens {
  const mode = payload?.modes?.find((candidate) => candidate.mode_id === modeId);

  return {
    background: modeColor(mode, "background") ?? colorToken(payload, "background") ?? "#F6F8FB",
    borderRadius: payload?.tokens?.radius?.md ?? payload?.tokens?.radius?.sm ?? 8,
    buttonText: colorScaleToken(payload, "primary")?.contrast ?? colorToken(payload, "text") ?? "#FFFFFF",
    fontFamily: payload?.tokens?.typography?.font_family ?? "Inter, sans-serif",
    padding: payload?.tokens?.spacing?.md ?? 16,
    primary: colorScaleToken(payload, "primary")?.main ?? colorToken(payload, "primary") ?? "#1D6F68",
    surface: modeColor(mode, "surface") ?? colorToken(payload, "surface") ?? "#FFFFFF",
    text: modeColor(mode, "text") ?? colorToken(payload, "text") ?? "#17211D"
  };
}

function modeColor(mode: ThemeMode | undefined, key: string): string | undefined {
  return mode?.color_overrides[key];
}

function colorToken(payload: ThemePayload | undefined, key: string): string | undefined {
  const token = payload?.tokens?.colors?.[key];
  return typeof token === "string" ? token : undefined;
}

function colorScaleToken(payload: ThemePayload | undefined, key: string): ThemeColorScale | undefined {
  const token = payload?.tokens?.colors?.[key];
  return typeof token === "object" && token !== null && !Array.isArray(token) ? token : undefined;
}
