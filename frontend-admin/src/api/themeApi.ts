import { adminApiClient, type AdminApiClient } from "./adminApiClient";

export type ThemeRevisionStatus = "draft" | "validated" | "published" | "archived" | "rejected";

export type ThemeRevisionSummary = {
  payload?: unknown;
  revision: number;
  schema_version: string;
  status: ThemeRevisionStatus;
  version: string;
};

export type ThemeSummary = {
  current_revision: ThemeRevisionSummary | null;
  description: string;
  name: string;
  theme_id: string;
};

type ThemeListResponse = {
  themes: ThemeSummary[];
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

export function countThemesByStatus(themes: ThemeSummary[], status: ThemeRevisionStatus): number {
  return themes.filter((theme) => theme.current_revision?.status === status).length;
}
