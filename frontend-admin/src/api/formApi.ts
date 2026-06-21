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
  calculation?: FormRule;
  field_id: string;
  field_type: string;
  help_text?: string;
  label: string;
  options?: { label: string; value: string }[];
  read_only?: boolean;
  required?: boolean;
  validation?: Record<string, unknown>;
  visibility?: FormRule;
};

export type FormRule = {
  expression: string;
  rule_type: string;
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

export type FormPropertyRow = {
  label: string;
  value: string;
};

export type FormFieldPropertySummary = {
  field_id: string;
  label: string;
  rows: FormPropertyRow[];
};

export type FormLogicRuleSummary = {
  expression: string;
  field_id: string;
  field_label: string;
  kind: "calculation" | "visibility";
  rule_type: string;
};

export type FormValidationRuleSummary = {
  field_id: string;
  field_label: string;
  rule: string;
  value: string;
};

export type FormPreviewItem = {
  field_id: string;
  label: string;
  options: string[];
  placeholder: string;
  read_only: boolean;
  required: boolean;
  type: "checkbox" | "date" | "file" | "number" | "select" | "text" | "unsupported";
};

type FormListResponse = {
  forms: FormSummary[];
};

type FormDetailResponse = {
  form: FormDetail;
};

type FormUpdateResponse = {
  draft_revision: FormRevisionSummary;
  form: FormDetail;
};

type FormPublishResponse = {
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

export async function updateFormDraft(
  formId: string,
  payload: FormPayload,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<FormUpdateResponse> {
  const result = await client.put<FormUpdateResponse, FormPayload>(
    `/forms/${encodeURIComponent(formId)}/`,
    payload,
    { query: { tenant } }
  );

  if (!result.data || !isRecord(result.data.form) || !isRecord(result.data.draft_revision)) {
    throw new Error("Form update response did not include form and draft revision objects.");
  }

  return result.data;
}

export async function publishFormRevision(
  formId: string,
  revision: number,
  client: AdminApiClient = adminApiClient,
  tenant = "demo"
): Promise<FormDetail> {
  const result = await client.post<FormPublishResponse, Record<string, never>>(
    `/forms/${encodeURIComponent(formId)}/revisions/${revision}/publish/`,
    {},
    { query: { tenant } }
  );

  if (!result.data || !isRecord(result.data.form)) {
    throw new Error("Form publish response did not include a form object.");
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

export function getFormPropertyRows(payload: FormPayload | undefined): FormPropertyRow[] {
  if (!payload) {
    return [];
  }

  return [
    { label: "Form id", value: payload.form_id },
    { label: "Version", value: payload.version },
    { label: "Mode", value: payload.mode },
    { label: "Entity", value: payload.entity_type ?? "not set" },
    { label: "Layout", value: payload.layout?.type ?? "single_column" },
    { label: "Fields", value: String(payload.fields.length) }
  ];
}

export function getFormFieldPropertySummaries(payload: FormPayload | undefined): FormFieldPropertySummary[] {
  return (payload?.fields ?? []).map((field) => ({
    field_id: field.field_id,
    label: field.label,
    rows: [
      { label: "Type", value: formatFieldType(field.field_type) },
      { label: "Binding", value: field.binding.data_path },
      { label: "Required", value: field.required ? "yes" : "no" },
      { label: "Read only", value: field.read_only ? "yes" : "no" },
      { label: "Options", value: String(field.options?.length ?? 0) },
      { label: "Validation", value: String(Object.keys(field.validation ?? {}).length) }
    ]
  }));
}

export function getFormLogicRuleSummaries(payload: FormPayload | undefined): FormLogicRuleSummary[] {
  return (payload?.fields ?? []).flatMap((field) => {
    const rules: FormLogicRuleSummary[] = [];

    if (field.visibility) {
      rules.push({
        expression: field.visibility.expression,
        field_id: field.field_id,
        field_label: field.label,
        kind: "visibility",
        rule_type: field.visibility.rule_type
      });
    }

    if (field.calculation) {
      rules.push({
        expression: field.calculation.expression,
        field_id: field.field_id,
        field_label: field.label,
        kind: "calculation",
        rule_type: field.calculation.rule_type
      });
    }

    return rules;
  });
}

export function getFormValidationRuleSummaries(payload: FormPayload | undefined): FormValidationRuleSummary[] {
  return (payload?.fields ?? []).flatMap((field) =>
    Object.entries(field.validation ?? {})
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([rule, value]) => ({
        field_id: field.field_id,
        field_label: field.label,
        rule: formatRuleName(rule),
        value: String(value)
      }))
  );
}

export function getFormPreviewItems(payload: FormPayload | undefined): FormPreviewItem[] {
  return (payload?.fields ?? []).map((field) => ({
    field_id: field.field_id,
    label: field.label,
    options: (field.options ?? []).map((option) => option.label),
    placeholder: previewPlaceholder(field),
    read_only: Boolean(field.read_only),
    required: Boolean(field.required),
    type: previewType(field.field_type)
  }));
}

function formatFieldType(fieldType: string): string {
  return fieldType
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function previewType(fieldType: string): FormPreviewItem["type"] {
  if (["text", "time", "barcode_qr", "signature"].includes(fieldType)) {
    return "text";
  }
  if (fieldType === "number") {
    return "number";
  }
  if (fieldType === "date") {
    return "date";
  }
  if (["boolean", "checkbox"].includes(fieldType)) {
    return "checkbox";
  }
  if (["select", "multi_select", "radio"].includes(fieldType)) {
    return "select";
  }
  if (["file", "image"].includes(fieldType)) {
    return "file";
  }

  return "unsupported";
}

function previewPlaceholder(field: FormField): string {
  if (field.help_text) {
    return field.help_text;
  }

  if (field.options?.length) {
    return `${field.options.length} options`;
  }

  return field.read_only ? "Read only value" : `Enter ${field.label.toLowerCase()}`;
}

function formatRuleName(rule: string): string {
  return rule
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
