# Plugin SDK Guide

This guide describes the current module/plugin SDK baseline. It is for contributors designing extension points, module manifests, compatibility rules, and future publishing flow.

## SDK Model

Plugins are represented as modules. A module declares its identity, compatibility, dependencies, permissions, configuration schemas, and runtime surfaces through a manifest.

The manifest schema lives at:

```text
contracts/schemas/v1/module-manifest.schema.json
```

Backend registration stores and validates the manifest through `ModuleRegistration` in:

```text
backend/apps/modules/models.py
```

The current SDK is intentionally local and repository-bound. External packaging, marketplace distribution, and signed third-party plugin uploads should build on this manifest contract instead of bypassing it.

## Manifest Fields

Required fields:

- `schema_version`: currently `v1`.
- `module_id`: stable lower_snake_case identifier.
- `name`: human-readable module name.
- `version`: semantic module version.
- `platform_min_version`: minimum compatible platform version.
- `plugin_api_version`: plugin API compatibility marker.
- `surfaces`: backend, frontend admin, and/or mobile surface metadata.

Optional fields:

- `description`: maintainer-facing description.
- `platform_max_version`: maximum compatible platform version.
- `runtime_min_version` and `runtime_max_version`: mobile runtime compatibility bounds.
- `dependencies`: required or optional module dependencies.
- `configuration_schemas`: schema references owned by the module.
- `permissions`: capability or permission codes exposed by the module.
- `extensions`: explicit extension bag for future metadata.

Keep the manifest deterministic. Generated contract outputs, validation, release manifests, and future plugin publishing should all be able to reproduce the same module metadata from the same manifest.

## Backend Extension Points

Backend contributions are declared under `surfaces.backend`:

```json
{
  "surfaces": {
    "backend": {
      "django_app": "backend.apps.example",
      "api_schema": "example.openapi.json",
      "jobs": ["example_rebuild_index"],
      "events": ["example.item.created"]
    }
  }
}
```

Rules:

- Put feature behavior in the owning Django app, not in `backend/apps/modules`.
- Keep registration and compatibility behavior in `backend/apps/modules`.
- Put shared primitives in `backend/apps/core`.
- Add migrations for model changes.
- Add service tests before view-level integration.
- Add manifest schema fixtures when metadata shape changes.

See `docs/developer/BACKEND_MODULES.md` for backend implementation details.

## Frontend Admin Extension Points

Frontend admin contributions map to the admin module registry:

```text
frontend-admin/src/modules/moduleRegistry.ts
```

The current static registry uses `AdminModuleContribution` records for navigation, route metadata, icon selection, capability checks, and view selection.

Rules:

- Keep `id` and `routePath` stable.
- Use capabilities that match backend and manifest permission language.
- Use icons from the design-system icon registry.
- Add route, shell, permission, and registry tests for new module surfaces.
- Keep placeholder views only for modules without an implemented workspace.

See `docs/developer/FRONTEND_MODULES.md` for frontend implementation details.

## Mobile Runtime Extension Points

Mobile runtime contributions are declared under `surfaces.mobile` and interpreted by the KMP runtime baseline.

Current mobile-facing contribution concepts:

- widgets;
- actions;
- sync handlers;
- theme mappings;
- navigation graphs;
- screens;
- forms;
- package download, verification, and local storage boundaries.

Rules:

- Do not render unverified package content.
- Keep shared runtime behavior in `mobile/shared`.
- Keep platform app entry points thin.
- Add common tests for runtime decoding, registry, offline, and sync behavior.
- Keep runtime compatibility aligned with `contracts/COMPATIBILITY_MATRIX.md`.

See `docs/mobile-runtime/RUNTIME_GUIDE.md` for runtime implementation details.

## Dependencies And Compatibility

Dependencies use `module_id`, `version_constraint`, and `optional`.

Rules enforced today:

- A module cannot depend on itself.
- A dependency can only be declared once.
- Required dependencies must be registered or enabled.
- Optional dependencies may be absent.
- Registered dependency versions must satisfy the constraint.

Supported constraint operators are `=`, `>`, `>=`, `<`, and `<=`. Use comma-separated ranges for bounded compatibility, for example:

```text
>=0.1.0,<0.2.0
```

Compatibility fields must be updated when platform, schema, runtime, or plugin API contracts change. Breaking schema changes require a new schema major version folder.

## Security Rules

Plugin SDK work is security-sensitive because plugins can affect backend behavior, admin navigation, mobile rendering, and sync.

Rules:

- Validate manifests before persistence.
- Do not load executable code from untrusted package content.
- Do not store secrets in manifests, fixtures, package payloads, or docs.
- Keep permissions explicit and least-privilege.
- Keep package verification ahead of local activation.
- Audit module registration, activation, deprecation, and removal events when those flows are implemented.
- Treat third-party publishing and marketplace workflows as future signed-release work, not as a local shortcut.

## Publishing Flow

The current repository does not publish external plugins yet. The baseline publishing flow should be:

1. Validate manifest schema and fixtures.
2. Validate backend, frontend, and mobile surfaces.
3. Validate dependency and compatibility ranges.
4. Build or collect module artifacts.
5. Generate SBOM metadata where package dependencies are involved.
6. Sign release artifacts.
7. Register the module in staging.
8. Promote only after CI, security, and compatibility checks pass.

Until external publishing exists, module changes should be merged through ordinary tracked issues and PRs.

## Validation Commands

For manifest and SDK documentation changes:

```powershell
python contracts/validate_contracts.py
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

For backend implementation changes:

```powershell
python tools/validate_backend.py
python tools/validate_python.py
```

For frontend implementation changes:

```powershell
cd frontend-admin
npm ci
npm run validate
```

For mobile implementation changes:

```powershell
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
```

## Test Expectations

SDK-related changes should include focused coverage for:

- valid and invalid manifests;
- dependency validation;
- compatibility boundaries;
- permission declarations;
- backend registration parity;
- frontend registry uniqueness and route behavior;
- mobile runtime decoding and verification behavior;
- docs validation when contributor-facing contracts change.
