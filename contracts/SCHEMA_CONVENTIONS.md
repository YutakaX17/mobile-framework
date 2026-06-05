# Schema Conventions

This document defines the initial contract rules for JSON Schemas in this repository.

Schemas are the source of truth for configuration packages. Backend, admin frontend, mobile runtime, Rust helpers, and generated types must follow these contracts rather than inventing separate shapes.

## Schema Location

Store JSON Schemas under `contracts/schemas`.

Use this layout:

```text
contracts/schemas/
  v1/
    module-manifest.schema.json
    theme.schema.json
    form.schema.json
    field.schema.json
    app.schema.json
    screen.schema.json
    component.schema.json
    action.schema.json
    workflow.schema.json
    sync-rule.schema.json
    deployment-package.schema.json
```

Fixtures live under:

```text
contracts/fixtures/
  valid/
    v1/
  invalid/
    v1/
```

Generated types live under `contracts/generated` and must be reproducible by CI.

## Naming

- Use kebab-case file names.
- End schema files with `.schema.json`.
- Use stable, descriptive schema names, for example `deployment-package.schema.json`.
- Use lower_snake_case for JSON property names because package payloads must be language-neutral and easy to consume from Python, TypeScript, Kotlin, and Rust.
- Use plural property names only for arrays.
- Use `*_id` for identifiers that refer to another object.
- Use `*_version` for semantic or schema versions.
- Use `created_at`, `updated_at`, `published_at`, and similar fields for timestamps.

## Schema Identity

Every schema must include:

- `$schema`
- `$id`
- `title`
- `type`
- `additionalProperties`

Use `$id` values in this form:

```text
https://schemas.mobile-framework.local/v1/<schema-name>.schema.json
```

The domain is intentionally non-production for now. If a real public schema registry is created later, update this through an ADR and keep redirects or migration notes.

## Versioning

Schema versions are explicit and path-based.

- Current initial schema version: `v1`.
- Backward-compatible additions remain in the same major schema folder.
- Breaking changes require a new major schema folder, for example `v2`.
- Every deployment package includes `schema_version`.
- Every mobile runtime declares supported schema versions through the compatibility matrix.

Backward-compatible changes include:

- Adding an optional property.
- Adding an enum value only when existing runtimes safely ignore or reject unknown values with a useful error.
- Tightening documentation without changing validation behavior.

Breaking changes include:

- Removing a property.
- Renaming a property.
- Changing a property type.
- Making an optional property required.
- Changing enum semantics.
- Changing runtime behavior expected from the same schema payload.

## Required Validation Behavior

Schemas must be strict enough to protect runtime safety:

- Use `additionalProperties: false` for stable objects unless an extension object is explicitly defined.
- Use `required` for fields needed by backend validation or mobile runtime execution.
- Use `enum` for known type discriminators such as widget, action, state, mode, or channel names.
- Use `format` for date-time and URI-like values where appropriate.
- Use bounded string lengths for names, slugs, labels, descriptions, and identifiers.
- Use arrays with `items` definitions.
- Use clear discriminators where a schema supports multiple object variants.

Extension points must be explicit. Prefer an `extensions` object over allowing arbitrary extra top-level properties.

## Compatibility Fields

Configuration packages and module manifests must include compatibility metadata early:

- `schema_version`
- `platform_min_version`
- `platform_max_version` when applicable
- `runtime_min_version`
- `runtime_max_version` when applicable
- `plugin_api_version` when applicable
- `modules`

Mobile clients must reject packages outside their supported schema/runtime range and continue using the last known good package.

## Fixture Rules

Every schema needs fixtures before it is considered usable:

- At least one valid fixture.
- At least one invalid fixture for missing required fields.
- At least one invalid fixture for an unsupported type or enum value where relevant.
- Invalid fixtures should fail for one clear reason each.

Fixture names should explain intent:

```text
valid/v1/theme-basic.json
invalid/v1/theme-missing-name.json
invalid/v1/theme-unknown-mode.json
```

## Generated Types

Generated types are planned for:

- Python backend.
- TypeScript admin frontend.
- Kotlin mobile runtime.

Generated output should either be committed or reproducible in CI. The project must choose the exact generator in a later implementation task before generated types become required.

## Security And Runtime Safety

Schemas must not permit arbitrary code execution.

Allowed configuration behavior:

- Select shipped widgets.
- Select shipped actions.
- Bind data to supported components.
- Configure validation rules supported by the runtime.
- Configure workflow transitions supported by the backend/runtime contract.

Disallowed configuration behavior:

- Downloaded scripts.
- Arbitrary Kotlin, JavaScript, Python, Rust, SQL, or shell code.
- Dynamic imports from package payloads.
- Unvalidated HTML rendering.

## Review Checklist

For every schema change, check:

- Does the change preserve mobile runtime compatibility?
- Does the package still validate through fixtures?
- Are generated types refreshed or intentionally deferred?
- Are backend, frontend, and mobile consumers updated or unaffected?
- Are tenant, permission, and audit-relevant fields explicit?
- Is the compatibility matrix updated if version support changed?
