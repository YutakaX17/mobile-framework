# Admin User Guide

This guide describes the current administrator-facing admin shell baseline. It documents what is available today and where future user guides will add deeper workflows.

## Access Model

Admin access is role and capability based.

Current roles:

- `platform-admin`: full access through wildcard capability `*`.
- `builder`: app, form, and theme builder access.
- `operator`: dashboard, workflow, and deployment access.

Current capabilities:

- `dashboard:view`
- `apps:manage`
- `forms:manage`
- `themes:manage`
- `workflows:manage`
- `deployments:manage`

If a user does not have the required capability for a module, the route shows an unauthorized state instead of the module workspace.

## Navigation

The admin shell builds navigation from the admin module registry. Current modules are ordered as:

1. Dashboard
2. Apps
3. Forms
4. Themes
5. Workflows
6. Deployments

Each module has a top-level route:

- `/dashboard`
- `/apps`
- `/forms`
- `/themes`
- `/workflows`
- `/deployments`

Some modules also have detail routes:

- `/apps/:appId`
- `/forms/:formId`
- `/themes/:themeId`

Unknown routes show an empty placeholder state.

## Dashboard

The dashboard is the operational landing surface. It is available to users with `dashboard:view` or `platform-admin`.

Use the dashboard to orient around platform status and active module areas. Detailed operational metrics and incident views are future guide topics.

## Apps

The Apps module is available to users with `apps:manage` or `platform-admin`.

Current app builder surfaces include:

- app list;
- app definition detail route;
- screen builder canvas baseline;
- component registry summaries;
- navigation and permission binding visibility;
- publish draft flow baseline.

Use `/apps` to review available apps and `/apps/:appId` to inspect a specific app definition.

## Forms

The Forms module is available to users with `forms:manage` or `platform-admin`.

Current form builder surfaces include:

- form list;
- form designer route;
- toolbox and canvas baseline;
- properties panel baseline;
- conditional logic and validation rule visibility;
- preview baseline;
- submission endpoint contract coverage.

Use `/forms` to review forms and `/forms/:formId` to inspect a specific form definition.

## Themes

The Themes module is available to users with `themes:manage` or `platform-admin`.

Current theme builder surfaces include:

- theme list;
- theme detail route;
- token detail baseline;
- contrast checker;
- live preview baseline;
- asset reference baseline;
- publish, rollback, and editing workflow baselines.

Use `/themes` to review themes and `/themes/:themeId` to inspect a specific theme definition.

## Workflows

The Workflows module is available to users with `workflows:manage` or `platform-admin`.

Current workflow surfaces include:

- workflow editor baseline;
- workflow schema support;
- state-machine validation;
- simulator baseline;
- task inbox baseline;
- execution log baseline.

Detailed workflow authoring steps will be documented in the workflow builder guide.

## Deployments

The Deployments module is available to users with `deployments:manage` or `platform-admin`.

Current deployment surfaces are represented by the deployment manager module and backend deployment package baselines:

- package model;
- compiler;
- signing;
- hash verification;
- release channels;
- activation and rollback;
- mobile manifest/download endpoints;
- audit events.

Detailed package promotion, rollback, and staging procedures will be documented in deployment and operations guides.

## Troubleshooting Access

If a module is not visible or shows an unauthorized state:

1. Confirm the user is signed in.
2. Confirm the user has a role with the required capability.
3. Confirm the module route is registered.
4. Confirm the route path matches the expected top-level route.
5. Confirm the module is not only available as a future placeholder.

For local development, role capability mapping lives in:

```text
frontend-admin/src/auth/permissions.ts
```

Module navigation metadata lives in:

```text
frontend-admin/src/modules/moduleRegistry.ts
```

## Current Limitations

Some modules have baseline or placeholder behavior while deeper workflows are being implemented. This guide documents current navigation and access rules; feature-specific guides should own detailed step-by-step instructions for each builder or operations workflow.

## Validation

Documentation-only changes to admin guides should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Admin frontend behavior changes should also run:

```powershell
cd frontend-admin
npm ci
npm run validate
```
