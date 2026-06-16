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

export type FormField = {
  binding: {
    data_path: string;
    entity_type?: string;
  };
  field_id: string;
  field_type: string;
  help_text?: string;
  label: string;
  options?: { label: string; value: string }[];
  read_only?: boolean;
  required?: boolean;
  validation?: Record<string, unknown>;
};

export type FormLayoutSection = {
  field_ids: string[];
  label: string;
  section_id: string;
};

export type FormPayload = {
  description?: string;
  entity_type?: string;
  fields: FormField[];
  form_id: string;
  layout?: {
    sections?: FormLayoutSection[];
    type?: string;
  };
  mode: "embedded" | "standalone";
  name: string;
  schema_version: string;
  status?: FormRevisionStatus;
  version: string;
};

export type FormDetail = FormSummary;

export type FormCanvasSection = {
  fields: FormField[];
  label: string;
  section_id: string;
};

export type FormToolboxItem = {
  count: number;
  field_type: string;
  label: string;
};

type FormListResponse = {
  forms: FormSummary[];
};

type FormDetailResponse = {
  form: FormDetail;
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

export async function fetchFormDetail(
  formId: string,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<FormDetail> {
  const result = await client.get<FormDetailResponse>(`/forms/${encodeURIComponent(formId)}/`, {
    query: { tenant }
  });

  if (!result.data || !isRecord(result.data.form)) {
    throw new Error("Form detail response did not include a form object.");
  }

  return result.data.form;
}

export function countFormsByStatus(forms: FormSummary[], status: FormRevisionStatus): number {
  return forms.filter((form) => form.current_revision?.status === status).length;
}

export function getFormPayload(form: FormDetail): FormPayload | undefined {
  const payload = form.current_revision?.payload;
  if (!isRecord(payload) || !Array.isArray(payload.fields)) {
    return undefined;
  }

  return payload as FormPayload;
}

export function getFormToolboxItems(payload: FormPayload | undefined): FormToolboxItem[] {
  const counts = new Map<string, number>();

  for (const field of payload?.fields ?? []) {
    counts.set(field.field_type, (counts.get(field.field_type) ?? 0) + 1);
  }

  return [...counts.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([field_type, count]) => ({
      count,
      field_type,
      label: formatFieldType(field_type)
    }));
}

export function getFormCanvasSections(payload: FormPayload | undefined): FormCanvasSection[] {
  if (!payload) {
    return [];
  }

  const fieldsById = new Map(payload.fields.map((field) => [field.field_id, field]));
  const sections = payload.layout?.sections ?? [];

  if (sections.length === 0) {
    return [
      {
        fields: payload.fields,
        label: "Fields",
        section_id: "fields"
      }
    ];
  }

  return sections.map((section) => ({
    fields: section.field_ids
      .map((fieldId) => fieldsById.get(fieldId))
      .filter((field): field is FormField => Boolean(field)),
    label: section.label,
    section_id: section.section_id
  }));
}

function formatFieldType(fieldType: string): string {
  return fieldType
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
