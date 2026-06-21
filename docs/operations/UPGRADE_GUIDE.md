# Upgrade Guide

This guide describes the current upgrade baseline for the mobile framework. It focuses on version inventory, pre-upgrade checks, database safety, schema compatibility, deployment package compatibility, rollback planning, and validation.

## Current Baseline

The current platform is pre-1.0. Upgrade work should be treated as controlled maintenance, not as a fully automated production upgrade process.

Current version sources:

- backend platform version: `backend/apps/modules/services.py`;
- frontend-admin version: `frontend-admin/package.json`;
- Rust extension version: `backend/rust_ext/Cargo.toml`;
- schema version: `contracts/schemas/v1`;
- compatibility matrix: `contracts/COMPATIBILITY_MATRIX.md`;
- release manifest generator: `tools/generate_release_manifest.py`.

The current compatibility target is platform `0.1.x`, schema `v1`, mobile runtime min `0.1.0`, mobile runtime max `0.1.x`, and plugin API `0`.

## Upgrade Scope

An upgrade can affect:

- Django backend code and migrations;
- frontend-admin assets and dependencies;
- Rust extension code and generated wheels;
- contract schemas and generated types;
- deployment package compiler behavior;
- mobile runtime compatibility;
- plugin/module manifest compatibility;
- CI and release workflows;
- operational documentation.

Do not treat a dependency bump as isolated if it changes generated package shape, schema behavior, runtime compatibility, or deployment artifacts.

## Pre-Upgrade Checklist

Before starting an upgrade:

1. Confirm the target commit, branch, or release version.
2. Review `contracts/COMPATIBILITY_MATRIX.md`.
3. Review pending migrations and model changes.
4. Take a fresh PostgreSQL backup for shared environments.
5. Confirm rollback expectations for code, database, deployment packages, and mobile runtime compatibility.
6. Confirm all required CI checks pass on the source branch.
7. Confirm dependency update PRs are reviewed for security and compatibility notes.
8. Confirm docs that mention changed behavior are in scope for the same upgrade.

For production-like environments, do not continue without a known-good backup and a tested restore path.

## Version Inventory

Before release or promotion, record:

- backend platform version from `CURRENT_PLATFORM_VERSION`;
- frontend-admin version from `frontend-admin/package.json`;
- Rust extension version from `backend/rust_ext/Cargo.toml`;
- schema folder and validation manifest version;
- mobile runtime compatibility range;
- plugin API compatibility level;
- release manifest output.

Generate a dry-run release manifest:

```powershell
python tools/generate_release_manifest.py --version 0.1.0
```

Use the manifest to confirm component versions and required artifacts before promotion.

## Database Upgrade Steps

For Django model or migration changes:

1. Take a database backup.
2. Record the backup checksum.
3. Run backend tests locally.
4. Apply migrations in a non-production environment.
5. Run smoke tests against the migrated database.
6. Validate tenant-scoped data and JSON payload compatibility.
7. Promote only after rollback expectations are clear.

Local validation:

```powershell
python tools/validate_backend.py
python tools/validate_foundation.py
```

If migrations change JSON payload expectations, also run contract validation.

## Contract And Schema Upgrades

Schemas live under `contracts/schemas`.

Rules:

- Compatible `v1` changes can stay under `contracts/schemas/v1`.
- Breaking schema changes require a new major schema folder, such as `v2`.
- Fixtures and generated types must be updated with schema changes.
- Mobile runtime package parsing changes must be reflected in the compatibility matrix.
- Deployment package changes must preserve hash and signature validation behavior.

Run:

```powershell
python contracts/validate_contracts.py
```

Update `contracts/COMPATIBILITY_MATRIX.md` whenever package shape, runtime behavior, schema compatibility, or plugin compatibility changes.

## Frontend And Backend Upgrades

For backend upgrades:

- review settings and environment variables;
- run backend validation;
- confirm migrations;
- confirm API error contracts still match callers;
- confirm deployment package, form, app, theme, workflow, and module payload validation still passes.

For frontend-admin upgrades:

- review `frontend-admin/package.json`;
- update lockfile changes intentionally;
- run frontend validation;
- confirm app, form, theme, workflow, and deployment views still render expected states.

Run:

```powershell
python tools/validate_backend.py
cd frontend-admin
npm run validate
```

## Rust Extension Upgrades

For Rust extension changes:

- review `backend/rust_ext/Cargo.toml`;
- confirm the PyO3 extension still builds;
- confirm Python wrapper behavior remains compatible;
- run Rust validation;
- run Python validation when Python integration changes.

Run:

```powershell
python tools/validate_rust.py
python tools/validate_python.py
```

## Deployment Package Compatibility

Deployment packages declare:

- `schema_version`;
- `runtime_min_version`;
- `runtime_max_version`;
- `platform_version`;
- app version;
- package hash;
- signature.

Before activating upgraded packages:

1. Confirm package payload validates against the deployment package schema.
2. Confirm hash validation passes.
3. Confirm signature handling matches the target environment.
4. Confirm mobile runtime compatibility covers target devices.
5. Confirm rollback package exists for the same app and channel.
6. Confirm release channel expectations in the compatibility matrix.

Package rollback activates a previous compatible package. It does not edit a package payload.

## Plugin And Module Compatibility

Module compatibility is checked against platform version constraints.

Before upgrading platform or module versions:

- confirm module manifests validate;
- confirm `platform_min_version` is not greater than the platform version;
- confirm `platform_max_version` does not exclude the platform version;
- update the compatibility matrix if plugin API expectations change.

The plugin API remains `0` in the current matrix until the extension API is formalized.

## Rollback Plan

Every upgrade should have a rollback plan that covers:

- code branch or release tag to redeploy;
- database restore point;
- active deployment package to reactivate;
- mobile runtime compatibility constraints;
- frontend-admin asset rollback;
- operational owner and approval path.

Rollback is simplest when the database schema remains backward compatible. If an upgrade includes destructive migrations, test restore before release and document the recovery window.

## Troubleshooting

If validation fails after an upgrade:

1. Identify whether the failure is backend, frontend, mobile, Rust, contract, or workflow related.
2. Check whether generated files or fixtures are stale.
3. Confirm the compatibility matrix matches the changed behavior.
4. Confirm package hashes were recalculated after payload changes.
5. Confirm dependency versions and lockfiles are intentional.

If mobile clients reject packages:

1. Confirm package `schema_version`.
2. Confirm runtime min and max versions.
3. Confirm package hash and signature.
4. Confirm the client supports the release channel package shape.

If rollback is needed:

1. Stop promotion.
2. Preserve logs and artifacts.
3. Restore or redeploy the previous known-good version.
4. Reactivate the previous compatible deployment package when applicable.
5. Verify application health before reopening writes.

## Validation Commands

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Upgrade behavior changes should run the affected validators and usually include:

```powershell
python tools/validate_backend.py
python contracts/validate_contracts.py
python tools/validate_rust.py
cd frontend-admin
npm run validate
```
