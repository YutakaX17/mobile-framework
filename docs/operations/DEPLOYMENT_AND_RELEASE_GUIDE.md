# Deployment And Release Guide

This guide describes the current deployment and release baseline. It focuses on deployment package structure, hash and signature handling, release channels, activation and rollback behavior, mobile delivery endpoints, staging deployment plans, and release manifests.

## Current Baseline

Deployment and release automation is implemented as a dry-run baseline with schema-validated deployment packages and workflow-generated release artifacts.

Current capabilities:

- deployment package model and compiler;
- canonical package hash calculation;
- HMAC package signature helper;
- release channel model;
- package activation;
- rollback to archived packages;
- mobile active manifest endpoint;
- mobile package download endpoint;
- deployment audit events;
- dry-run staging deployment plan;
- dry-run release manifest.

Real production deployment still requires environment credentials, approval gates, and operational runbooks to be configured outside this baseline.

## Deployment Packages

Deployment packages are immutable tenant-scoped mobile configuration packages.

Required package payload fields:

- `schema_version`;
- `package_id`;
- `tenant_id`;
- `app_id`;
- `app_version`;
- `runtime_min_version`;
- `runtime_max_version`;
- `modules`;
- `theme`;
- `app`;
- `forms`;
- `created_at`;
- `created_by`;
- `hash`;
- `signature`.

Optional package payload fields include `platform_version`, `channel`, `assets`, `sync_rules`, and `extensions`.

Package payloads embed the app revision payload, theme revision payload, form revision payloads, and module manifests needed by the mobile runtime. The deployment package schema remains the source of truth for the payload shape.

## Hashes And Signatures

Package hashes are calculated from canonical unsigned package JSON.

Hash rules:

- `hash` and `signature` are removed before canonical JSON is generated.
- JSON keys are sorted.
- Compact separators are used.
- The digest is SHA-256.
- The stored value uses the `sha256:<hex>` format.

The package model verifies that the stored hash matches the canonical unsigned payload hash before saving.

Package signatures use the helper format `hmac-sha256:<hex>` when a signing key is provided. The compiler can also use a placeholder signature for the current baseline while still calculating and validating the package hash.

## Release Channels

Supported release channels are:

- `dev`;
- `test`;
- `staging`;
- `production`.

Deployment channels are tenant-scoped and unique by tenant and channel. The helper that creates default channels creates all four channels for a tenant.

Package records are unique by tenant and package id, and also by tenant, app id, app version, and channel. This prevents two packages with the same app version from occupying the same channel for the same tenant.

## Activation

Deployment packages use these statuses:

- `signed`;
- `active`;
- `archived`.

Activation rules:

1. The package must already be saved.
2. Archived packages cannot be activated.
3. Activating a package archives any other active package for the same tenant, app id, and channel.
4. The selected package is marked `active`.
5. A deployment audit event is recorded when the package was not already active.

Use activation to promote a signed package into the active package slot for a channel.

## Rollback

Rollback promotes an archived package back to active.

Rollback rules:

- The channel must be supported.
- An active package must currently exist for the tenant, app id, and channel.
- The rollback target must be archived.
- If no package id is provided, the most recently updated archived package is selected.
- The current active package is archived.
- The target package is marked active.
- A deployment audit event records the previous active package id.

Rollback does not edit package payloads. It changes which immutable package is active for the channel.

## Mobile Delivery Endpoints

The backend exposes two mobile delivery endpoints.

Active package manifest:

- Accepts `GET` only.
- Requires a `tenant` query parameter.
- Requires an `app_id` query parameter.
- Accepts optional `channel`, defaulting to `dev`.
- Returns active package metadata for the app and channel.
- Returns 404 when no active package exists.

Package download:

- Accepts `GET` only.
- Requires a `tenant` query parameter.
- Looks up a package by package id.
- Requires the package to be `active`.
- Returns package metadata and the full package payload.
- Sets the `ETag` header to the package hash.

Mobile clients should use the manifest to discover the active package, then download the package by id and verify the hash before applying it.

## Staging Deployment Plan

The staging deployment workflow generates a dry-run deployment plan artifact.

The plan generator validates that these prerequisites exist:

- `backend/Dockerfile`;
- `frontend-admin/Dockerfile`;
- `.github/workflows/docker-build.yml`;
- `.github/workflows/image-signing.yml`;
- `.github/workflows/sbom-generation.yml`.

The generated plan includes:

- schema version `staging-deployment-plan.v1`;
- environment `staging`;
- mode `dry-run`;
- repository name;
- pre-deploy checks;
- backend service metadata;
- frontend-admin service metadata;
- promotion gates.

Current staging services are the backend and frontend-admin containers. The backend depends on Postgres and Redis. The frontend-admin service depends on the backend.

## Release Manifest

The release workflow generates a dry-run release manifest artifact.

The manifest generator requires a semantic release version and validates that release prerequisites exist, including CI workflows, Dockerfiles, SBOM tooling, staging deployment tooling, and the compatibility matrix.

The manifest records:

- release version;
- generation time;
- repository;
- backend component version;
- frontend-admin component version;
- Rust extension version;
- contracts schema version;
- mobile runtime compatibility range;
- required checks;
- required artifacts;
- release steps.

Required artifacts include the SPDX SBOM, backend image signing bundle, frontend-admin image signing bundle, and staging deployment plan.

## Promotion Checklist

Before promoting a package or release beyond the dry-run baseline:

1. Confirm all required checks pass on `main`.
2. Confirm deployment package payloads validate against the deployment package schema.
3. Confirm package hashes match canonical unsigned payloads.
4. Confirm signatures use the approved signing key or production signing mechanism.
5. Confirm target release channel is enabled for the tenant.
6. Confirm an activation or rollback plan is documented.
7. Confirm staging secrets and environment credentials are configured.
8. Confirm image signing and SBOM artifacts are retained.
9. Confirm mobile runtime compatibility covers the target devices.
10. Confirm rollback target packages are available before production promotion.

## Troubleshooting

If a deployment package does not save:

1. Confirm the payload validates against the deployment package schema.
2. Confirm model fields match payload fields such as `package_id`, `app_id`, `app_version`, channel, hash, and signature.
3. Confirm the channel is one of `dev`, `test`, `staging`, or `production`.
4. Confirm the payload hash matches the canonical unsigned package hash.

If activation fails:

1. Confirm the package has been saved.
2. Confirm the package is not archived.
3. Confirm another active package can be archived for the same app and channel.

If rollback fails:

1. Confirm the channel is valid.
2. Confirm an active package exists.
3. Confirm the target package exists and is archived.
4. If no package id is provided, confirm at least one archived package exists for the app and channel.

If mobile manifest lookup fails:

1. Confirm `tenant` and `app_id` query parameters are present.
2. Confirm the tenant exists.
3. Confirm the requested channel is valid.
4. Confirm an active package exists for the app and channel.

If package download fails:

1. Confirm the package id exists for the tenant.
2. Confirm the package status is `active`.
3. Confirm the client uses the returned `ETag` hash for cache and integrity checks.

## Validation Commands

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Deployment package behavior changes should also run:

```powershell
python tools/validate_backend.py
python contracts/validate_contracts.py
```

Release or staging script changes should also run:

```powershell
python tools/generate_staging_deployment_plan.py
python tools/generate_release_manifest.py --version 0.1.0
```
