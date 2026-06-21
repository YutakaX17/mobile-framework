# Backend Module Guide

This guide describes the current backend module baseline. It is for contributors adding or changing module-facing backend behavior in the Django control plane.

## Current Shape

Backend modules are registered through `ModuleRegistration` in `backend/apps/modules/models.py`. The model stores the module identity, version, compatibility data, dependency declarations, status, and the original JSON manifest.

The registration lifecycle is intentionally strict:

1. A module manifest is submitted or constructed.
2. `ModuleRegistration.from_manifest()` maps manifest fields onto model fields.
3. `ModuleRegistration.clean()` validates the manifest shape and checks field parity.
4. Compatibility and dependency checks run before saving.
5. `save()` calls `full_clean()` so invalid registrations cannot be persisted accidentally.

## Module Manifest

The manifest schema lives at:

```text
contracts/schemas/v1/module-manifest.schema.json
```

Required fields:

- `schema_version`: currently `v1`.
- `module_id`: stable lower_snake_case identifier.
- `name`: human-readable module name.
- `version`: semantic module version.
- `platform_min_version`: minimum platform version supported by the module.
- `plugin_api_version`: plugin API compatibility marker.
- `surfaces`: backend, frontend admin, and/or mobile contribution metadata.

Common optional fields:

- `description`: maintainer-facing summary.
- `platform_max_version`: upper platform compatibility bound.
- `runtime_min_version` and `runtime_max_version`: mobile runtime compatibility bounds.
- `dependencies`: other modules required or optionally used by this module.
- `configuration_schemas`: JSON Schema references owned by the module.
- `permissions`: permission codes exposed by the module.
- `extensions`: explicit extension bag for future metadata.

Keep manifest fields deterministic. Validation and generated contract outputs assume stable JSON content and predictable schema names.

## Backend Surface

The backend surface declares Django-facing contributions:

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

Use `django_app` for the Python import path of the Django app that owns models, services, views, and migrations. Use `jobs` for background job names registered through the backend job registry. Use `events` for event names published through the core event bus.

Current app boundaries:

- `backend/apps/core`: shared backend primitives such as events, jobs, errors, and service lifecycle.
- `backend/apps/modules`: module registration and compatibility validation.
- `backend/apps/configurations`: configuration registry and schema-backed validation.
- `backend/apps/audit`: audit event model baseline.
- Feature apps such as `themes`, `form_builder`, `app_builder`, `deployment_packages`, `sync`, and `workflow_builder` own their domain behavior.

Do not put feature-specific business logic into `backend/apps/modules`; that app should stay focused on module metadata and compatibility.

## Compatibility Rules

Compatibility validation is implemented in `backend/apps/modules/services.py`.

Rules enforced today:

- Versions must be semantic version strings.
- `platform_min_version` cannot be greater than `platform_max_version`.
- A module cannot require a platform version newer than the current platform.
- A module cannot cap support below the current platform.

The current platform version is defined by `CURRENT_PLATFORM_VERSION` in `backend/apps/modules/services.py`. Update compatibility documentation and tests whenever that value or the version policy changes.

## Dependency Rules

Dependencies are declared in the manifest:

```json
{
  "dependencies": [
    {
      "module_id": "identity",
      "version_constraint": ">=0.1.0",
      "optional": false
    }
  ]
}
```

Rules enforced today:

- A module cannot depend on itself.
- A dependency can only be declared once per manifest.
- Required dependencies must exist in `registered` or `enabled` status.
- Optional dependencies may be absent.
- Registered dependency versions must satisfy the declared version constraint.

Supported version constraint operators are `=`, `>`, `>=`, `<`, and `<=`. Use comma-separated clauses for bounded ranges, for example `>=0.1.0,<0.2.0`.

## Adding Backend Module Behavior

When adding a backend module contribution:

1. Add or update the manifest schema only when the metadata shape changes.
2. Add fixtures under `contracts/fixtures/` when schema behavior changes.
3. Add Django models and migrations inside the owning app, not inside `modules` unless the change is module-registration behavior.
4. Add services for business rules that should be testable without views.
5. Add API views only after the service behavior is covered.
6. Add permissions to the manifest when admin or API access control depends on them.
7. Update docs and generated contract outputs when schemas change.

Keep module identifiers stable. Renaming a module should be treated as a migration and compatibility decision, not a simple label edit.

## Validation Commands

Run these for backend module changes:

```powershell
python contracts/validate_contracts.py
python tools/validate_backend.py
python tools/validate_python.py
python tools/validate_foundation.py
```

For documentation-only changes to this guide:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

## Test Expectations

Backend module changes should cover:

- Valid and invalid manifest schema behavior.
- Field parity between manifest content and `ModuleRegistration`.
- Platform compatibility boundaries.
- Required, optional, duplicate, self, and unsatisfied dependencies.
- Migration checks for model changes.
- Service-level behavior before view-level integration.

Prefer focused tests around the owning service or model before adding broad integration coverage.
