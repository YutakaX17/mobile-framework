# Target Architecture

## High-Level Architecture

The platform has three coordinated layers:

1. Backend control plane.
2. Admin builder frontend.
3. Mobile runtime.

The backend stores and validates source-of-truth configuration. The admin frontend lets users edit that configuration through friendly builders. The mobile runtime downloads signed configuration packages and renders approved app behavior.

## Recommended Repository Structure

```text
mobile-framework/
  backend/
    apps/
      core/
      tenants/
      identity/
      modules/
      app_builder/
      form_builder/
      workflow_builder/
      theme_builder/
      deployments/
      sync/
      audit/
    rust_ext/
    tests/
    pyproject.toml
  frontend-admin/
    src/
      app/
      modules/
      builders/
      design-system/
      generated/
      tests/
    package.json
  mobile/
    composeApp/
    shared/
    androidApp/
    iosApp/
    desktopApp/
  contracts/
    schemas/
    graphql/
    openapi/
    generated/
  infra/
    compose/
    docker/
    github-actions/
    observability/
  docs/
    adr/
    developer/
    admin/
    mobile-runtime/
    plugin-sdk/
```

## Backend Architecture

Use Django as the main backend because it is strong for admin workflows, ORM-backed business models, auth, permissions, migrations, and productivity.

Use Rust through PyO3 and maturin only where it is clearly valuable:

- Configuration package compilation.
- JSON Schema validation acceleration.
- App definition diffing.
- Sync merge and conflict helpers.
- Cryptographic hashing/signing helpers.
- High-volume rules evaluation.
- Potentially CPU-heavy transformations.

Do not use Rust for normal CRUD or ordinary admin features until there is a measured reason.

### Backend Core Modules

#### `core`

Responsibilities:

- Platform settings.
- Shared model base classes.
- Event bus.
- Module manifest loading.
- Configuration registry.
- Error model.
- Health checks.
- Background job primitives.

#### `tenants`

Responsibilities:

- Tenant model.
- Tenant settings.
- Tenant-specific app packages.
- Tenant-specific themes.
- Tenant isolation rules.

#### `identity`

Responsibilities:

- Users.
- Roles.
- Permissions.
- Groups.
- Authentication.
- Sessions/tokens.
- MFA hooks.

#### `modules`

Responsibilities:

- Backend module registry.
- Module metadata.
- Dependency checks.
- Compatibility checks.
- Enable/disable lifecycle.
- Module configuration validation.

#### `app_builder`

Responsibilities:

- App definitions.
- Navigation trees.
- Screens.
- Layout definitions.
- Component placement.
- Action bindings.
- Publish states.

#### `form_builder`

Responsibilities:

- Form definitions.
- Field schemas.
- Validation rules.
- Form submissions.
- Form-to-data bindings.
- Field/control registry.

#### `workflow_builder`

Responsibilities:

- Workflow definitions.
- Task definitions.
- Approval rules.
- State transitions.
- Triggers and handlers.
- Workflow simulation.

#### `theme_builder`

Responsibilities:

- Design tokens.
- Theme definitions.
- Accessibility validation.
- Preview data.
- Theme publishing.

#### `deployments`

Responsibilities:

- App package creation.
- Package signing.
- Channels such as dev, staging, production.
- Rollback.
- Version compatibility.
- Mobile update manifests.

#### `sync`

Responsibilities:

- Mobile sync endpoints.
- Sync sessions.
- Change logs.
- Conflict detection.
- Conflict resolution.
- Device registration.

#### `audit`

Responsibilities:

- Audit events.
- Mutation logs.
- Configuration revision history.
- Admin activity logs.

## API Architecture

Recommended API shape:

- GraphQL for admin builder workflows where flexible queries help.
- REST or GraphQL persisted queries for mobile runtime.
- OpenAPI for operational endpoints and integrations.
- WebSockets or Server-Sent Events for admin preview/deployment status.

Important rule:

Mobile runtime endpoints should be stable, small, and cacheable. Do not expose the entire admin GraphQL surface to mobile clients.

## Configuration Package Architecture

A published mobile app package should include:

- `package_id`
- `tenant_id`
- `app_id`
- `app_version`
- `runtime_min_version`
- `runtime_max_version`
- `schema_version`
- `modules`
- `theme`
- `navigation`
- `screens`
- `forms`
- `workflows`
- `permissions`
- `data_models`
- `sync_rules`
- `assets`
- `created_at`
- `created_by`
- `hash`
- `signature`

The package is immutable after publication. Rollback means activating a previous package, not editing an already published package.

## Admin Frontend Architecture

Use Vite + React + TypeScript.

Recommended libraries:

- Router: TanStack Router or React Router.
- State: TanStack Query for server state, Zustand or Redux Toolkit for local builder state - use redux.
- Forms: React Hook Form plus Zod or Valibot.
- Drag/drop: dnd-kit.
- Schema validation: Ajv for JSON Schema.
- UI system: MUI, Radix, or shadcn-style components, but keep a platform-specific design system layer.
- Icons: lucide-react or the selected UI system icon library.

Frontend module contributions should support:

- Routes.
- Navigation entries.
- Builder panels.
- Property editors.
- Field controls.
- Theme preview components.
- Translations.
- Permission guards.
- Runtime previews.

## Mobile Runtime Architecture

Use Kotlin Multiplatform with Compose Multiplatform.

Core mobile modules:

- Runtime kernel.
- Auth module.
- Config package downloader.
- Package verifier.
- Theme mapper.
- Navigation renderer.
- Screen renderer.
- Widget registry.
- Form renderer.
- Offline database.
- Sync engine.
- Conflict inbox.
- Logging/diagnostics.

Recommended mobile libraries:

- Networking: Ktor client.
- Serialization: kotlinx.serialization.
- Database: SQLDelight.
- Dependency injection: Koin or manual DI.
- Background work: platform-specific adapters behind shared interfaces.
- Secure storage: platform-specific secure storage wrappers.

## Data Architecture

Server:

- PostgreSQL is the source of truth.
- Use JSONB only for flexible configuration, not for everything.
- Core entities should have explicit relational models.
- Configuration definitions should be JSONB plus schema version plus validation status.

Mobile:

- SQLite stores local data, config package, sync queue, and cached reference data.
- Use SQLDelight migrations.
- All offline mutations are stored in an outbox before sync.

## Sync Architecture

Use an explicit sync protocol:

- Device registers with server.
- Device downloads active package manifest.
- Device downloads required package/assets.
- Device pulls changed reference/data records since cursor.
- Device writes local actions to an outbox.
- Device pushes outbox batches.
- Server validates and accepts/rejects/conflicts each change.
- Device stores sync result and updates local records.

Required sync metadata:

- `entity_type`
- `entity_id`
- `tenant_id`
- `version`
- `changed_at`
- `changed_by`
- `deleted_at`
- `device_id`
- `sync_cursor`
- `conflict_state`

