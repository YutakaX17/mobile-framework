# Frontend Admin

Vite, React, and TypeScript admin builder frontend. The current scaffold provides the app entrypoint, an operational admin shell, initial route map, and local validation wiring.

## Routing

Initial admin navigation is defined in `src/app/routes.tsx` and currently registers:

- `/dashboard`
- `/apps`
- `/forms`
- `/themes`
- `/workflows`
- `/deployments`

## API Client

The initial typed API client lives in `src/api/adminApiClient.ts`. It defaults to `/api` and can be pointed at another backend by setting `VITE_ADMIN_API_BASE_URL`.

## Auth Shell

The initial auth shell lives in `src/auth` and protects admin routes behind a development login view. It is intentionally local state only until backend auth endpoints are added.

## Module Registry

Admin navigation and workspace metadata are sourced from `src/modules/moduleRegistry.ts`, which provides the first typed contribution registry for future frontend modules.

## Design System

The design token foundation lives in `src/design-system/tokens.ts`. Shell CSS consumes the same token names as custom properties under the `--mf-*` prefix.

## Icon System

Admin shell icons are registered in `src/design-system/icons.tsx` and rendered through `AdminIcon`, currently backed by Lucide React.

## Local Validation

Install and validate from the repository root:

```powershell
python tools/validate_frontend_admin.py
```

Equivalent direct commands from `frontend-admin/`:

```powershell
npm ci
npm run validate
```

## Planned Areas

- `src/app`: application shell, routing, auth, permissions, global layout. Initial shell, route foundation, and login view exist.
- `src/api`: typed API client foundation and request/error primitives.
- `src/auth`: local auth session model, provider, and guard helpers.
- `src/modules`: typed frontend module contribution registry.
- `src/builders`: theme, form, app/screen, workflow, and deployment builders.
- `src/design-system`: typed tokens, icons, components, accessibility helpers, previews. Initial token and icon foundations exist.
- `src/generated`: generated contract/API types.
- `src/tests`: shared test utilities and smoke tests.
