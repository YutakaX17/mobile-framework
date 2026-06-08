# MVP Scope

This document defines the first useful platform slice. It exists to keep implementation focused and to prevent early work from expanding into a full no-code product before the platform kernel is proven.

## MVP Goal

Build a minimal, end-to-end platform where an administrator can configure a simple mobile app package and a mobile runtime can safely render it, work offline for form submission, and sync submitted data back to the backend.

The MVP proves these claims:

- Configuration packages can be typed, versioned, validated, and signed.
- The mobile runtime can render supported configuration without executing downloaded code.
- Forms, themes, navigation, package publication, offline outbox, sync, permissions, and audit can work together in one coherent flow.
- The architecture can grow through modules without making configuration an untyped JSON blob.

## MVP Users

The MVP supports four user groups at a basic level:

- Platform administrator: sets up the initial tenant, users, roles, release channel, and package publication flow.
- App configurator: creates one simple themed app with one form screen.
- Mobile end user: downloads the active package, opens the app, submits a form offline, and syncs later.
- Developer: extends and validates platform behavior through typed schemas, tests, and module boundaries.

## In Scope

### Tenant And Identity

- One operational tenant for the first MVP path.
- Tenant-scoped records in backend models and APIs from the beginning.
- Username/password login.
- Role and permission basics.
- Permission checks for builder and publish operations.

### Contracts And Package Model

- JSON Schemas for initial module manifest, theme, field, form, action, screen, app, and deployment package definitions.
- Valid and invalid fixtures for contract validation.
- Contract validation command in local development and CI.
- Compatibility matrix for platform, schema, mobile runtime, and plugin API versions.
- Immutable package shape with hash/signature fields.

### Backend Kernel

- Django project scaffold.
- Environment-specific settings for local, test, and production-like deployment.
- PostgreSQL for persistent server data.
- Core app with health endpoint and structured error pattern.
- Tenant model.
- Identity/RBAC baseline or clear integration with Django auth.
- Module registry model and manifest validation service.
- Configuration registry and revision model.
- Audit event model for important writes.
- Package publication skeleton that validates contracts before activation.

### Admin Frontend

- Vite, React, and TypeScript shell.
- Login shell and guarded routes.
- Operational dashboard after login.
- Module-aware navigation placeholder.
- Theme Builder MVP.
- Form Builder MVP.
- Simple App Builder with navigation and one form screen.
- Validate and publish flow for a package.

### Mobile Runtime

- Kotlin Multiplatform scaffold.
- Package manifest download.
- Package hash/signature verification interface.
- Last-known-good package storage.
- Dynamic rendering for basic navigation, screen, theme, and form fields.
- Offline form submission storage.
- Outbox push when online.
- Basic sync status visibility.

### Sync

- Device registration skeleton.
- Pull active package manifest.
- Push form submission outbox batch.
- Accept/reject response handling.
- Sync session audit logs.

### Audit And Quality

- Audit logs for configuration changes, publish actions, package activation, role/permission changes, and sync rejection events.
- CI foundation workflow.
- Contract tests.
- Backend tests for registry, tenant isolation, permissions, and package validation once backend exists.
- Frontend and mobile smoke tests once those surfaces exist.

## Out Of Scope For MVP

These are intentionally deferred:

- Plugin marketplace.
- Public plugin publishing workflow.
- Arbitrary scripting or downloaded executable code.
- Complex workflow automation and visual workflow builder.
- Advanced analytics.
- Deep integration builder.
- Multi-tenant self-service onboarding UI.
- App store deployment automation.
- Complex conflict resolution UI beyond controlled accept/reject/manual-review placeholders.
- Advanced report builder.
- Full observability stack beyond structured logs and basic health checks.
- Full SSO/OIDC and MFA implementation, though architecture should not block them.
- Generated native apps per customer.

## MVP Success Criteria

The MVP is successful when:

- A valid deployment package can be produced from typed configuration.
- Invalid configuration fails with useful validation errors.
- A mobile runtime can download, verify, store, and render the package.
- A mobile user can submit a form offline and sync it later.
- Backend records the submission and audit trail.
- Tenant and permission boundaries are enforced in the backend path.
- CI validates contracts and relevant tests before merge.
- Documentation explains setup, package compatibility, and the supported MVP path.

## Non-Negotiable Constraints

- Do not execute arbitrary downloaded code on mobile clients.
- Do not treat JSONB as a replacement for core relational models.
- Do not publish mutable packages; rollback activates a prior package.
- Do not expose broad admin APIs directly to mobile clients.
- Do not delay tenant and permission checks until after feature work.
- Do not add Rust business logic before a narrow helper boundary is justified.

## First End-To-End Scenario

1. Administrator logs in.
2. Administrator confirms one tenant and basic roles exist.
3. App configurator creates a theme.
4. App configurator creates a patient intake form.
5. App configurator creates an app with one navigation item and one form screen.
6. App configurator validates and publishes a package to the `dev` channel.
7. Mobile runtime downloads the active manifest and package.
8. Mobile runtime verifies the package and applies it.
9. Mobile user completes the form offline.
10. Mobile runtime stores the submission in the outbox.
11. Mobile runtime syncs when online.
12. Backend accepts the submission and records audit/sync logs.
