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

The typed API client lives in `src/api/adminApiClient.ts`. It defaults to `/api`, sends same-origin session credentials, and can be pointed at another backend by setting `VITE_ADMIN_API_BASE_URL`.

For local development, Vite proxies `/api` to Django at `http://127.0.0.1:8000`. Start the backend separately before using the live admin workflow:

```powershell
python backend/manage.py runserver 127.0.0.1:8000
```

## Auth Shell

The auth shell lives in `src/auth` and protects admin routes behind Django session authentication. The login view uses `GET /api/auth/csrf/`, `POST /api/auth/login/`, `GET /api/auth/session/`, and `GET /api/auth/tenants/` to load the current user and demo tenant context. Use the seeded local account `demo-admin` / `demo-admin-password` after running `seed_demo_mvp`.

## Module Registry

Admin navigation and workspace metadata are sourced from `src/modules/moduleRegistry.ts`, which provides the first typed contribution registry for future frontend modules.

## Design System

The design token foundation lives in `src/design-system/tokens.ts`. Shell CSS consumes the same token names as custom properties under the `--mf-*` prefix.

## Icon System

Admin shell icons are registered in `src/design-system/icons.tsx` and rendered through `AdminIcon`, currently backed by Lucide React.

## Shell Layout

The shell layout keeps sidebar navigation, topbar actions, workspace content, skip navigation, and the authenticated user menu in `src/app/AdminShell.tsx`. Topbar action metadata lives in `src/app/shellLayoutModel.ts`.

## Permissions

The initial permissions guard lives in `src/auth/permissions.ts`. Admin routes compare authenticated user roles against module contribution capabilities before rendering protected workspaces.

## Error Boundary

The app is wrapped by `src/app/ErrorBoundary.tsx` so render failures show a stable recovery view instead of a blank screen.

## Notifications

The local notification system lives in `src/app/NotificationProvider.tsx` and `src/app/notificationModel.ts`. Shell actions enqueue accessible notifications through the shared provider.

## Theme Builder

The `/themes` workspace renders the initial read-only theme list page. `/themes/:themeId` renders the first token detail baseline for color, typography, spacing, radius, mode, asset reference, contrast, and live preview inspection. Theme API helpers live in `src/api/themeApi.ts`, including draft update support for the editing workflow baseline.

## Form Builder

The `/forms` workspace renders the initial read-only form list page backed by `src/api/formApi.ts`. `/forms/:formId` renders the first form designer baseline with field toolbox, canvas, properties, conditional logic, validation rule, and mobile preview inspection.

## Testing

Vitest is the unit test runner. Shared fixture builders live in `src/tests/testFixtures.ts` for auth users, module contributions, and notifications.

Playwright smoke tests live in `src/tests/smoke` and run through `npm run smoke`. The repository validation command runs unit tests, production build checks, and the smoke suite.

## Local Validation

Install and validate from the repository root:

```powershell
python tools/validate_frontend_admin.py
```

Equivalent direct commands from `frontend-admin/`:

```powershell
npm ci
npx playwright install chromium
npm run validate
```

## Planned Areas

- `src/app`: application shell, routing, auth, permissions, global layout. Initial shell layout, route foundation, and login view exist.
- `src/api`: typed API client foundation and request/error primitives.
- `src/auth`: local auth session model, provider, permission helpers, and guard helpers.
- `src/modules`: typed frontend module contribution registry.
- `src/builders`: theme, form, app/screen, workflow, and deployment builders.
- `src/design-system`: typed tokens, icons, components, accessibility helpers, previews. Initial token and icon foundations exist.
- `src/generated`: generated contract/API types.
- `src/tests`: shared test utilities and smoke tests. Initial fixture builders exist.
