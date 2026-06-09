# Backend

Django control plane for tenants, identity, module registry, configuration registry, package publication, sync, and audit.

## Current Scaffold

The backend includes a minimal Django project:

- `manage.py`: Django command entrypoint.
- `config/settings/base.py`: shared settings.
- `config/settings/dev.py`: local development settings.
- `config/settings/test.py`: test settings.
- `config/settings/prod.py`: production-like environment-driven settings.
- `config/urls.py`: root URL configuration.
- `apps/core`: initial core app with `GET /health/` and reusable service lifecycle baseline.
- `apps/tenants`: initial tenant model baseline.
- `apps/identity`: initial role, permission, and tenant-scoped user assignment baseline.
- `apps/modules`: initial module registry and manifest validation baseline.
- `apps/configurations`: initial tenant-scoped configuration definition and revision registry baseline.
- `apps/audit`: initial tenant-scoped and platform-level audit event model baseline.

## Local Validation

Install backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Run backend validation from the repository root:

```powershell
python tools/validate_backend.py
```

Equivalent direct commands:

```powershell
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test apps.core apps.tenants apps.identity apps.modules apps.configurations apps.audit --settings=config.settings.test
```

## Planned Areas

- `apps/core`: shared kernel, health checks, event bus, service lifecycle, error model. Initial service lifecycle baseline exists.
- `apps/tenants`: tenant model and isolation rules. Initial tenant model baseline exists.
- `apps/identity`: users, roles, permissions, sessions, and MFA/OIDC hooks. Initial RBAC model baseline exists.
- `apps/modules`: module manifests, dependency checks, compatibility checks. Initial module registry baseline exists.
- `apps/configurations`: tenant-scoped definitions, revisions, status workflow, and schema validation. Initial configuration registry baseline exists.
- `apps/app_builder`: app definitions, navigation, screens, actions, publish states.
- `apps/form_builder`: form definitions, fields, validation, submissions.
- `apps/workflow_builder`: workflow definitions, state machines, tasks, simulation.
- `apps/theme_builder`: design tokens, theme validation, preview, publishing.
- `apps/deployments`: immutable package compilation, signing, channels, rollback.
- `apps/sync`: mobile sync protocol, outbox handling, conflict handling.
- `apps/audit`: mutation logs, config revisions, admin and sync audit events. Initial audit event model baseline exists.
- `rust_ext`: bounded PyO3/maturin helpers once contracts are stable.
