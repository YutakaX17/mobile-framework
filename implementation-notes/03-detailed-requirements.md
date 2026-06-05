# Detailed Requirements

## Backend Requirements

### Core Platform

- The backend must support a module-based architecture similar to openIMIS.
- Modules must be enabled through a manifest.
- Module dependencies must be validated at startup.
- Module versions must be checked against the platform version.
- Each module must be able to register:
  - Models.
  - API schema.
  - Permissions.
  - Background jobs.
  - Event handlers.
  - Configuration schemas.
  - Admin frontend contributions metadata.
  - Mobile runtime contributions metadata.
- The backend must expose health checks for API, database, cache, worker, and object storage.

### Tenancy

- The platform must support multiple tenants.
- Tenant data must be isolated.
- App definitions, themes, users, roles, packages, and sync data must be tenant-scoped.
- All API access must enforce tenant context.

### Authentication And Authorization

- Support secure username/password login.
- Support future SSO/OIDC.
- Support MFA-ready design.
- Support role-based access control.
- Support permission checks on every API operation.
- Support builder-specific permissions, such as:
  - Manage apps.
  - Manage forms.
  - Manage workflows.
  - Manage themes.
  - Publish packages.
  - Manage users.
  - View audit logs.
  - Manage integrations.

### Configuration Registry

- Store configuration as typed, versioned records.
- Validate every configuration against JSON Schema before saving.
- Keep draft, reviewed, published, archived states.
- Keep full revision history.
- Support rollback to previous published version.
- Support validation errors readable by non-technical users.
- Support export/import of configuration bundles.

### App Builder Domain

- Store app definitions.
- Store navigation definitions.
- Store screen definitions.
- Store screen components.
- Store actions and bindings.
- Store preview data.
- Validate all screens before publication.
- Prevent publishing if required modules or widgets are missing.

### Form Builder Domain

- Support text, number, date, time, boolean, select, multi-select, radio, checkbox, file, image, location, barcode/QR, signature, calculated, hidden, and custom fields.
- Support sections, repeat groups, conditional visibility, validation rules, required rules, and help text.
- Support standalone forms and embedded forms.
- Support draft and submitted states.
- Support mapping form data to backend entities.
- Support offline form submissions.
- Support schema migrations for form changes.

### Theme Builder Domain

- Support color tokens, typography tokens, spacing tokens, shape/radius tokens, elevation tokens, and component tokens.
- Support light and dark modes.
- Support logo and brand assets.
- Support live preview in admin frontend.
- Support mobile preview sizes.
- Enforce accessibility contrast checks.
- Prevent publishing inaccessible critical theme combinations unless an authorized override is recorded.

### Workflow Builder Domain

- Support visual state machines.
- Support approval workflows.
- Support task assignment rules.
- Support triggers:
  - Form submitted.
  - Entity created.
  - Entity updated.
  - Scheduled event.
  - Manual action.
  - Integration webhook.
- Support actions:
  - Create task.
  - Send notification.
  - Update entity.
  - Call integration.
  - Change workflow state.
- Support simulation before publishing.
- Support workflow versioning.

### Deployment Packages

- Published packages must be immutable.
- Packages must be signed.
- Packages must contain compatibility metadata.
- Packages must be assignable to release channels.
- Packages must support rollback.
- Packages must be downloadable by authorized mobile clients only.

### Mobile Sync

- Support offline-first mobile usage.
- Support reference data download.
- Support incremental sync.
- Support outbox push.
- Support conflict detection.
- Support conflict resolution policies.
- Support device registration.
- Support sync logs for troubleshooting.

### Audit

- Audit every configuration change.
- Audit every publish action.
- Audit every user/role/permission change.
- Audit every package activation/rollback.
- Audit mobile sync sessions and rejected changes.
- Audit integration calls.

## Admin Frontend Requirements

### General UX

- The first screen after login should be an operational dashboard, not a marketing page.
- Navigation must be predictable.
- Builder UI should be dense enough for repeated work but not cluttered.
- Every builder must show validation feedback.
- Every destructive action must require confirmation.
- Every publish action must show a summary of what will change.
- Use responsive layouts that work on laptop and desktop.
- Accessibility must be designed in from the beginning.

### App Builder

- Let users create apps.
- Let users configure navigation.
- Let users add screens.
- Let users drag components onto screens.
- Let users configure component properties.
- Let users bind components to data and actions.
- Let users preview screens in mobile sizes.
- Let users validate and publish.

### Form Builder

- Provide toolbox, canvas, and properties panel.
- Support drag/drop and keyboard-friendly alternatives.
- Support field grouping and reordering.
- Support validation rule editor.
- Support conditional logic editor.
- Support preview mode.
- Support schema view for advanced users.

### Theme Builder

- Provide token controls, not raw CSS editing as the primary flow.
- Include color picker, palette generator, typography selectors, spacing scale controls, and component previews.
- Show contrast results.
- Show app preview with real components.
- Support import/export of themes.

### Workflow Builder

- Provide visual states and transitions.
- Provide task assignment editor.
- Provide trigger/action editor.
- Provide validation and simulation results.
- Show workflow version status.

### Deployment Manager

- Show draft, reviewed, published, archived packages.
- Show package compatibility.
- Show active release channels.
- Show rollback options.
- Show mobile adoption/upgrade status.

## Mobile Runtime Requirements

### Runtime

- Download active package manifest.
- Verify package signature.
- Store package locally.
- Render navigation dynamically.
- Render screens dynamically.
- Render forms dynamically.
- Apply active theme dynamically.
- Support app update checks.
- Support graceful failure if package is incompatible.

### Offline

- Store local data in SQLite.
- Queue changes while offline.
- Retry sync when online.
- Show sync status to user.
- Preserve submitted data even if sync fails.
- Allow controlled conflict resolution.

### Security

- Store tokens securely.
- Use HTTPS only.
- Verify package signature before applying configuration.
- Never execute arbitrary downloaded code.
- Enforce permissions from package and server.
- Protect sensitive local data where platform APIs allow.

## Non-Functional Requirements

### Performance

- Admin builder must remain responsive with large app definitions.
- Mobile runtime must render common screens quickly.
- Sync must support batching.
- Config validation must provide fast feedback.
- Use Rust only where measurement or clear complexity justifies it.

### Reliability

- Backend must expose health checks.
- Workers must be restartable.
- Package publication must be transactional.
- Mobile must keep working with last valid package if update fails.

### Maintainability

- Use clear modules.
- Use generated types from shared schemas.
- Use ADRs for major architecture decisions.
- Keep docs close to code.

### Security

- Follow OWASP guidance.
- Run dependency scanning.
- Run static analysis.
- Protect secrets.
- Enforce least privilege.
- Log security-sensitive events.

