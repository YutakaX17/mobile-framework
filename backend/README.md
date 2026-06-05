# Backend

Django control plane for tenants, identity, module registry, configuration registry, package publication, sync, and audit.

## Planned Areas

- `apps/core`: shared kernel, health checks, event bus, service lifecycle, error model.
- `apps/tenants`: tenant model and isolation rules.
- `apps/identity`: users, roles, permissions, sessions, and MFA/OIDC hooks.
- `apps/modules`: module manifests, dependency checks, compatibility checks.
- `apps/app_builder`: app definitions, navigation, screens, actions, publish states.
- `apps/form_builder`: form definitions, fields, validation, submissions.
- `apps/workflow_builder`: workflow definitions, state machines, tasks, simulation.
- `apps/theme_builder`: design tokens, theme validation, preview, publishing.
- `apps/deployments`: immutable package compilation, signing, channels, rollback.
- `apps/sync`: mobile sync protocol, outbox handling, conflict handling.
- `apps/audit`: mutation logs, config revisions, admin and sync audit events.
- `rust_ext`: bounded PyO3/maturin helpers once contracts are stable.

No Django application code has been scaffolded yet.
