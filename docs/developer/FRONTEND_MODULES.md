# Frontend Module Guide

This guide describes the current admin frontend module baseline. It is for contributors adding navigation entries, protected workspaces, or module-facing UI surfaces in `frontend-admin/`.

## Current Shape

Admin modules are declared in:

```text
frontend-admin/src/modules/moduleRegistry.ts
```

The registry exports `AdminModuleContribution` records. These records drive:

- admin shell navigation ordering;
- route metadata in `frontend-admin/src/app/routes.tsx`;
- permission gating through `frontend-admin/src/auth/permissions.ts`;
- placeholder or feature-specific view selection;
- module registry tests.

The baseline is static and local to the frontend. Backend-driven module discovery can be added later, but it should preserve the same contribution shape and validation rules.

## Contribution Fields

Each `AdminModuleContribution` includes:

- `id`: stable module identifier.
- `label`: navigation label.
- `routePath`: top-level admin route, such as `/forms`.
- `section`: workspace section label shown in the shell.
- `summary`: short workspace description.
- `area`: one of `builder`, `core`, or `operations`.
- `icon`: icon name from the design-system icon registry.
- `capabilities`: permission capabilities required to access the module.
- `order`: numeric sort key for navigation order.

Example:

```ts
{
  area: "builder",
  capabilities: ["forms:manage"],
  icon: "forms",
  id: "forms",
  label: "Forms",
  order: 30,
  routePath: "/forms",
  section: "Form builder",
  summary: "Form definition workspace"
}
```

Keep `id` and `routePath` stable. Renaming either one should be treated as a compatibility decision because tests, deep links, permissions, and documentation may depend on them.

## Navigation And Routes

`getOrderedAdminModules()` sorts contributions by `order`, then by `label`. The route map in `frontend-admin/src/app/routes.tsx` derives `adminRoutes` from that ordered registry.

Top-level module routes are created from `routePath`. Some feature modules also have nested routes:

- `/apps/:appId` uses the `/apps` module metadata.
- `/forms/:formId` uses the `/forms` module metadata.
- `/themes/:themeId` uses the `/themes` module metadata.

When adding a feature-specific view:

1. Add or update the contribution in `moduleRegistry.ts`.
2. Add the view component under `frontend-admin/src/app/views/`.
3. Wire `getRouteView()` or a nested route in `routes.tsx`.
4. Add route and shell tests in `AdminShell.test.ts` or related route tests.
5. Keep placeholder views for modules that do not yet have a dedicated workspace.

## Permissions

Module access is capability-based. Capabilities are declared on each contribution and checked by `canAccessModule()`.

Current role mapping lives in:

```text
frontend-admin/src/auth/permissions.ts
```

Rules:

- A user must have every capability listed by the module.
- The `platform-admin` role grants `*`.
- Missing or unknown roles grant no capabilities.
- Unauthorized users see `UnauthorizedView` for protected routes.

When adding a new module capability:

1. Add the capability to the module contribution.
2. Add or update role capability mapping.
3. Add permission tests for allowed and denied users.
4. Keep permission strings consistent with backend and manifest documentation.

Use `domain:action` capability names such as `reports:manage` until a stricter permission catalog is introduced.

## Icons And Design System

The `icon` field must use an `IconName` from the design system. If a module needs a new icon:

1. Add it to the icon registry.
2. Add icon registry tests.
3. Reuse existing `lucide-react` icons when possible.
4. Avoid hand-drawn SVGs unless the icon system cannot represent the action.

Navigation should remain concise and scan-friendly. Long labels belong in `summary`, not the primary nav label.

## Registry Validation

The registry provides `validateAdminModuleRegistry()` and `registerAdminModule()` to catch duplicate `id` or `routePath` values.

Tests live in:

```text
frontend-admin/src/modules/moduleRegistry.test.ts
```

Expected coverage for registry changes:

- ordered route paths;
- lookup by route;
- duplicate id and route rejection;
- duplicate route path rejection;
- sorted insertion for newly registered modules;
- permission gating for new capabilities.

## Adding A Frontend Module

Use this checklist:

1. Define the module contribution in `moduleRegistry.ts`.
2. Confirm `routePath` is unique and starts with `/`.
3. Choose an existing `IconName` or add a tested icon.
4. Add capabilities and role mappings.
5. Add the workspace view component.
6. Wire `routes.tsx` for the top-level or nested route.
7. Add tests for registry ordering, route behavior, and permissions.
8. Update docs when the module introduces a new user-facing workflow.

## Validation Commands

Run these for frontend module changes:

```powershell
cd frontend-admin
npm ci
npm run validate
```

From the repository root, also run:

```powershell
python tools/validate_foundation.py
python tools/validate_python.py
```

For documentation-only changes to this guide:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

## Future Direction

The current static registry keeps early development simple. A later backend-driven registry should still validate duplicate routes, permission requirements, icon names, and view bindings before exposing module navigation in the admin shell.
