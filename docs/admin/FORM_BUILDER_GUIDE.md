# Form Builder Guide

This guide describes the current form builder baseline for administrators and builders. It focuses on the implemented form library, designer inspection panels, mobile preview, and submission contract behavior.

## Access

The Forms module is available to users with `forms:manage` or `platform-admin`.

Routes:

- `/forms`: form library.
- `/forms/:formId`: form designer and current revision inspection.

If the route shows an unauthorized state, confirm the user has the `builder` role or another role that grants `forms:manage`.

## Form Library

The form library lists tenant-scoped forms returned by the admin API.

Use the library to review:

- form identifier;
- form name and description;
- current revision status;
- current revision version;
- form mode;
- current revision field count;
- published form count;
- total form count.

The Refresh action reloads the form list. Loading, unavailable, and empty states are explicit so administrators can distinguish "no forms exist" from "forms could not load."

## Form Designer

The form designer shows the current revision payload for a selected form.

Current designer panels:

- field toolbox;
- canvas sections;
- form properties;
- field properties;
- conditional logic;
- validation rules;
- mobile preview.

If no payload is available, the designer shows a no-payload state instead of rendering partial form data.

## Field Toolbox

The field toolbox summarizes field types that are already present in the current form payload.

Each toolbox item shows:

- field type label;
- count of matching fields on the canvas.

Field type labels are derived from the payload field type by replacing underscores with spaces and title-casing each part. Keep field type names stable because the toolbox, preview, and mobile renderer depend on the same schema values.

## Canvas And Layout

Form payloads are schema-backed configuration packages. Required top-level fields include `schema_version`, `form_id`, `name`, `version`, `mode`, and `fields`.

The designer builds the canvas from `layout.sections` when sections are provided. Each section uses:

- `section_id`;
- `label`;
- `field_ids`.

If the payload does not define layout sections, the designer renders a single `Fields` section containing all fields in payload order.

Each canvas field shows the field label, field type, data binding, field identifier, and required state. The current baseline is an inspection surface; future editing controls should preserve schema validation before revisions are saved or published.

## Properties

The form properties panel summarizes:

- form id;
- version;
- mode;
- entity type;
- layout type;
- field count.

Each field property summary includes:

- field type;
- binding data path;
- required state;
- read-only state;
- option count;
- validation rule count.

Use this panel to verify that the form payload maps fields to the expected entity and data paths before a revision is published.

## Conditional Logic

Conditional logic summaries are collected from each field's `visibility` and `calculation` rules.

Each rule shows:

- field identifier;
- field label;
- rule kind;
- rule type;
- expression.

Review these summaries when forms depend on derived values or conditional visibility. Expressions should be reviewed against the target runtime before publishing because mobile packages use the same payload contract.

## Validation Rules

Validation rule summaries are collected from each field's `validation` object.

Rules are sorted by rule key and displayed with a formatted rule name and value. For example, `min_length` is displayed as `Min Length`.

Use validation summaries to confirm required constraints, ranges, patterns, and field-specific validation settings before the form is made available to users.

## Preview

The preview panel renders a mobile form approximation from the current payload.

Preview mapping:

- `text`, `time`, `barcode_qr`, and `signature` render as text inputs.
- `number` renders as a number input.
- `date` renders as a date input.
- `boolean` and `checkbox` render as checkboxes.
- `select`, `multi_select`, and `radio` render as select controls.
- `file` and `image` render as file inputs.
- unsupported field types render an unsupported placeholder.

Preview placeholders prefer `help_text`. If no help text exists, options show as an option count, read-only fields show `Read only value`, and other fields show an entry prompt based on the field label.

The preview is useful for layout and field review, but the schema and runtime renderer remain the source of truth for published mobile behavior.

## Submission Behavior

The backend exposes a form submission endpoint for published current revisions.

Submission rules:

- The endpoint accepts `POST` requests only.
- A `tenant` query parameter is required.
- The form must exist for the tenant.
- The form must have a current revision.
- The current revision status must be `published`.
- The request body must be a JSON object.
- The request body must include an `answers` object.

Accepted submissions create a `FormSubmission` with `received` status and return a submission summary containing the submission id, form id, revision, answer count, and status.

Mobile submission packages use the `mobile-form-submission` contract. Required fields are `schema_version`, `local_id`, `device_id`, `form_id`, `revision`, `submitted_at`, and `answers`. Optional metadata can include `app_id`, `package_version`, and `screen_id`.

## Troubleshooting

If the form list does not load:

1. Confirm the tenant query parameter is available to the API client.
2. Confirm the tenant exists.
3. Confirm the user can access the Forms module.
4. Check the admin API response shape includes a `forms` array.

If a form designer does not load:

1. Confirm the route contains a `formId`.
2. Confirm the form exists for the tenant.
3. Confirm the detail response includes a `form` object.
4. Confirm the current revision includes a payload with a `fields` array.

If canvas sections are incomplete:

1. Confirm `layout.sections` references existing field identifiers.
2. Confirm every expected field appears in the top-level `fields` array.
3. Confirm the payload validates against the form schema.

If submissions are rejected:

1. Confirm the request uses `POST`.
2. Confirm the `tenant` query parameter is present.
3. Confirm the form has a current revision.
4. Confirm the current revision is `published`.
5. Confirm the request body is a JSON object with an `answers` object.

## Validation

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Form builder behavior changes should also run:

```powershell
python tools/validate_backend.py
cd frontend-admin
npm run validate
```

Form schema or submission contract changes should run:

```powershell
python contracts/validate_contracts.py
```
