# Analysis Of Uploaded openIMIS Folders

This project should borrow the modular architecture ideas from the uploaded openIMIS sample folders, while improving schema typing, frontend modernization, and runtime safety.

## Uploaded Folder Summary

### `openimis-be_py-develop`

This is the backend assembly project.

Important patterns:

- Reads `openimis.json`.
- Loads configured backend modules.
- Adds modules to Django `INSTALLED_APPS`.
- Builds central GraphQL schema by importing each module's `schema.py`.
- Includes module URLs under each module name.
- Uses environment variables for deployment and database configuration.
- Supports background work through Celery.

Pattern to reuse:

- Manifest-driven module assembly.
- Central API composition.
- Environment-based deployment.
- Separate migration and worker processes.

Pattern to improve:

- Make module metadata stricter and typed.
- Add compatibility checks before startup.
- Avoid importing modules just to discover metadata where possible.

### `openimis-be-core_py-develop`

This is the backend core module.

Important patterns:

- `ModuleConfiguration` stores per-module JSON configuration.
- Base model types support UUIDs, validity dates, mutation logs, history, and JSON extensions.
- Core GraphQL mutation lifecycle logs writes, validates, sends signals, executes sync/async, and records status.
- Service signals let modules hook into service operations.
- Permissions are module-configurable.
- Security middleware, JWT, CSRF handling, rate limiting, and headers are included.

Pattern to reuse:

- Core module as the kernel.
- Runtime configuration table.
- Write/mutation logging.
- Validation, before, after lifecycle hooks.
- Permission codes or permission registry.
- Background task support.

Pattern to improve:

- Replace loose JSON configs with typed schemas.
- Store configuration revisions and validation status.
- Make errors structured and user-friendly.
- Use stronger API typing and generated clients.

### `openimis-be-form_builder_py-develop`

This is a backend form builder module.

Important patterns:

- `FormDefinition` stores schema and metadata.
- `FormSubmission` stores submitted data.
- Forms can be standalone or page extensions.
- Backend exposes GraphQL queries and mutations.
- README describes a control registry and JSON schema concept.

Pattern to reuse:

- Forms as configuration.
- Standalone and extension modes.
- Control registry.
- Submission status model.

Pattern to improve:

- Form schema must be formal JSON Schema, not an opaque JSON blob.
- Store revisions, publish states, migrations, and compatibility metadata.
- Add validation pipelines and data binding contracts.
- Avoid frontend/backend naming mismatch.

### `openimis-be-tasks_management_py-develop`

This is a backend task/workflow module.

Important patterns:

- `Task`, `TaskGroup`, and `TaskExecutor` models.
- Maker-checker style workflow through task creation and resolution.
- Service signals around task lifecycle.
- Configurable permission codes.
- Generic handlers can call service methods when tasks complete.

Pattern to reuse:

- Generic task engine.
- Workflow hooks around service operations.
- Task assignment and completion policies.

Pattern to improve:

- Model workflow definitions explicitly.
- Version workflow definitions.
- Add state-machine validation.
- Add visual builder support.
- Add workflow simulation and dry-run validation.

### `openimis-fe_js-develop`

This is the frontend assembly project.

Important patterns:

- Reads `openimis.json`.
- Generates module imports.
- Loads configured frontend modules.
- Provides `ModulesManager`.
- Modules contribute routes, menu entries, translations, refs, reports, reducers, and boot hooks.
- Supports theme and logo configuration.

Pattern to reuse:

- Frontend module contribution model.
- Route/menu/translation/ref registration.
- Assembly by manifest.

Pattern to improve:

- Use Vite, React, and TypeScript.
- Avoid generated CommonJS `require` for long-term module safety.
- Use typed module manifests.
- Use generated API clients.
- Modernize design system and theming.

### `openimis-fe-core_js-develop`

This is the frontend core module.

Important patterns:

- Application shell.
- Auth, routes, error boundaries, translations, dialogs.
- Generic components.
- Permission checks.
- Published component mechanism.

Pattern to reuse:

- Core UI shell.
- Published components and contributions.
- Centralized permission-aware routing.

Pattern to improve:

- Use modern React patterns.
- Use accessible components by default.
- Use design tokens for themes.
- Avoid overly broad generic components that are hard to type.

### `openimis-fe-form_builder_js-main`

This is a frontend form builder prototype.

Important patterns:

- Vite build.
- Drag and drop through `dnd-kit`.
- Toolbox, canvas, properties panel.
- Form renderer.
- GraphQL hooks.

Pattern to reuse:

- Builder surface concept.
- Drag/drop workflow.
- Properties inspector.
- Preview/render split.

Pattern to improve:

- Make schemas typed and shared across backend, frontend, and mobile.
- Use responsive professional builder UI.
- Add validation, undo/redo, preview modes, accessibility checks, and publish workflow.

### `openimis-fe-tasks_management_js-develop`

This is a frontend task management module.

Important patterns:

- Contributes pages, menus, actions, reducer, pickers, and task components.

Pattern to reuse:

- Workflow/task UI as a module.

Pattern to improve:

- Turn task management into a full workflow builder and workflow inbox.

### `openimis-dist_dkr-develop`

This is the Docker distribution folder.

Important patterns:

- Docker Compose includes frontend, backend, migrations, worker, Postgres, RabbitMQ, Redis/cache, and OpenSearch.
- Cypress E2E tests wait for the backend.
- NGINX/proxy configs are included.

Pattern to reuse:

- Dev/staging/prod container model.
- Separate migrations service.
- Separate worker process.
- End-to-end tests against a composed stack.

Pattern to improve:

- Add image signing, SBOMs, vulnerability scanning, environment separation, migration gates, and rollback plans.

## Main Lessons

1. Build a core kernel first.
2. Use module manifests for backend, frontend, and mobile modules.
3. Keep module configuration in the database, but make it typed, versioned, and auditable.
4. Centralize API composition.
5. Keep write logs and workflow events.
6. Use visual builders, but treat schemas as the source of truth.
7. Use Docker from the beginning.
8. Add strong testing and security gates before the system grows.

