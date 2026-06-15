# Frontend Admin

Vite, React, and TypeScript admin builder frontend. The current scaffold provides the app entrypoint, an operational admin shell placeholder, and local validation wiring.

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

- `src/app`: application shell, routing, auth, permissions, global layout. Initial shell scaffold exists.
- `src/modules`: frontend module contribution registry.
- `src/builders`: theme, form, app/screen, workflow, and deployment builders.
- `src/design-system`: tokens, components, accessibility helpers, previews.
- `src/generated`: generated contract/API types.
- `src/tests`: shared test utilities and smoke tests.
