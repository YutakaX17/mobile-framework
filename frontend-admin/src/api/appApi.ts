import { adminApiClient, type AdminApiClient } from "./adminApiClient";

export type AppRevisionStatus = "draft" | "reviewed" | "published" | "archived";

export type AppRevisionSummary = {
  navigation_count: number;
  permission_count: number;
  revision: number;
  schema_version: string;
  screen_count: number;
  status: AppRevisionStatus;
  version: string;
};

export type AppSummary = {
  app_id: string;
  current_revision: AppRevisionSummary | null;
  description: string;
  name: string;
};

type AppListResponse = {
  apps: AppSummary[];
};

export async function fetchAppSummaries(
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<AppSummary[]> {
  const result = await client.get<AppListResponse>("/apps/", { query: { tenant } });

  if (!result.data || !Array.isArray(result.data.apps)) {
    throw new Error("App list response did not include an apps array.");
  }

  return result.data.apps;
}

export function countAppsByStatus(apps: AppSummary[], status: AppRevisionStatus): number {
  return apps.filter((app) => app.current_revision?.status === status).length;
}
