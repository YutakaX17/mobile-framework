import { adminApiClient, type AdminApiClient } from "./adminApiClient";

export type FormRevisionStatus = "draft" | "reviewed" | "published" | "archived";

export type FormRevisionSummary = {
  field_count: number;
  payload?: unknown;
  revision: number;
  schema_version: string;
  status: FormRevisionStatus;
  version: string;
};

export type FormSummary = {
  current_revision: FormRevisionSummary | null;
  description: string;
  form_id: string;
  mode: "embedded" | "standalone";
  name: string;
};

type FormListResponse = {
  forms: FormSummary[];
};

export async function fetchFormSummaries(
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<FormSummary[]> {
  const result = await client.get<FormListResponse>("/forms/", { query: { tenant } });

  if (!result.data || !Array.isArray(result.data.forms)) {
    throw new Error("Form list response did not include a forms array.");
  }

  return result.data.forms;
}

export function countFormsByStatus(forms: FormSummary[], status: FormRevisionStatus): number {
  return forms.filter((form) => form.current_revision?.status === status).length;
}
