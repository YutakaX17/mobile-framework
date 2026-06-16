import { adminApiClient, type AdminApiClient } from "./adminApiClient";

export type ThemeRevisionStatus = "draft" | "validated" | "published" | "archived" | "rejected";

export type ThemeRevisionSummary = {
  payload?: unknown;
  revision: number;
  schema_version: string;
  status: ThemeRevisionStatus;
  version: string;
};

export type ThemeColorScale = {
  contrast?: string;
  dark?: string;
  light?: string;
  main?: string;
};

export type ThemeMode = {
  color_overrides: Record<string, string>;
  label: string;
  mode_id: string;
};

export type ThemePayload = {
  accessibility?: {
    contrast_standard?: string;
    override_recorded?: boolean;
    validated?: boolean;
  };
  modes?: ThemeMode[];
  name: string;
  schema_version: string;
  theme_id: string;
  tokens?: {
    colors?: Record<string, string | ThemeColorScale>;
    radius?: Record<string, number>;
    spacing?: Record<string, number>;
    typography?: {
      fallback_family?: string;
      font_family?: string;
      scale?: Record<
        string,
        {
          font_size?: number;
          font_weight?: number;
          letter_spacing?: number;
          line_height?: number;
        }
      >;
    };
  };
  version: string;
};

export type ThemeSummary = {
  current_revision: ThemeRevisionSummary | null;
  description: string;
  name: string;
  theme_id: string;
};

export type ThemeDetail = ThemeSummary;

export type ThemeTokenRow = {
  detail?: string;
  label: string;
  value: string;
};

type ThemeListResponse = {
  themes: ThemeSummary[];
};

type ThemeDetailResponse = {
  theme: ThemeDetail;
};

export async function fetchThemeSummaries(
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<ThemeSummary[]> {
  const result = await client.get<ThemeListResponse>("/themes/", { query: { tenant } });

  if (!result.data || !Array.isArray(result.data.themes)) {
    throw new Error("Theme list response did not include a themes array.");
  }

  return result.data.themes;
}

export async function fetchThemeDetail(
  themeId: string,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<ThemeDetail> {
  const result = await client.get<ThemeDetailResponse>(`/themes/${encodeURIComponent(themeId)}/`, {
    query: { tenant }
  });

  if (!result.data || !isRecord(result.data.theme)) {
    throw new Error("Theme detail response did not include a theme object.");
  }

  return result.data.theme;
}

export function countThemesByStatus(themes: ThemeSummary[], status: ThemeRevisionStatus): number {
  return themes.filter((theme) => theme.current_revision?.status === status).length;
}

export function getThemePayload(theme: ThemeDetail): ThemePayload | undefined {
  const payload = theme.current_revision?.payload;
  if (!isRecord(payload) || !isRecord(payload.tokens)) {
    return undefined;
  }

  return payload as ThemePayload;
}

export function getColorTokenRows(payload: ThemePayload | undefined): ThemeTokenRow[] {
  return Object.entries(payload?.tokens?.colors ?? {}).map(([label, token]) => {
    if (isRecord(token)) {
      return {
        detail: `contrast ${stringValue(token.contrast, "not set")}`,
        label,
        value: stringValue(token.main, "not set")
      };
    }

    return {
      label,
      value: String(token)
    };
  });
}

export function getNumberTokenRows(
  payload: ThemePayload | undefined,
  group: "radius" | "spacing"
): ThemeTokenRow[] {
  return Object.entries(payload?.tokens?.[group] ?? {}).map(([label, value]) => ({
    label,
    value: `${value}px`
  }));
}

export function getTypographyTokenRows(payload: ThemePayload | undefined): ThemeTokenRow[] {
  const typography = payload?.tokens?.typography;
  const scaleRows = Object.entries(typography?.scale ?? {}).map(([label, style]) => ({
    detail: `${style.font_weight ?? "default"} weight`,
    label,
    value: `${style.font_size ?? "?"}/${style.line_height ?? "?"}`
  }));

  if (!typography?.font_family) {
    return scaleRows;
  }

  return [
    {
      detail: typography.fallback_family ? `fallback ${typography.fallback_family}` : undefined,
      label: "font_family",
      value: typography.font_family
    },
    ...scaleRows
  ];
}

export function getModeRows(payload: ThemePayload | undefined): ThemeTokenRow[] {
  return (payload?.modes ?? []).map((mode) => ({
    detail: `${Object.keys(mode.color_overrides).length} color overrides`,
    label: mode.mode_id,
    value: mode.label
  }));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value ? value : fallback;
}
