# Backend

Django control plane for tenants, identity, module registry, configuration registry, package publication, sync, and audit.

## Current Scaffold

The backend includes a minimal Django project:

- `manage.py`: Django command entrypoint.
- `config/settings/base.py`: shared settings.
- `config/settings/database.py`: shared PostgreSQL database configuration helper.
- `config/settings/worker.py`: shared background worker configuration helper.
- `config/settings/dev.py`: local development settings.
- `config/settings/test.py`: test settings.
- `config/settings/prod.py`: production-like environment-driven settings.
- `config/urls.py`: root URL configuration.
- `apps/core`: initial core app with `GET /health/`, reusable service lifecycle baseline, in-process event bus baseline, API error model baseline, and background job registry baseline.
- `apps/tenants`: initial tenant model baseline.
- `apps/identity`: initial role, permission, and tenant-scoped user assignment baseline.
- `apps/modules`: initial module registry, manifest validation, dependency validation, and compatibility validation baseline.
- `apps/configurations`: initial tenant-scoped configuration definition and revision registry baseline.
- `apps/themes`: initial tenant-scoped theme model and revision baseline backed by shared theme schema validation.
- `apps/audit`: initial tenant-scoped and platform-level audit event model baseline.
- `rust_ext`: initial PyO3/maturin scaffold for bounded native helpers.

## Local Validation

Install backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Run backend validation from the repository root:

```powershell
python tools/validate_backend.py
```

Run Rust extension validation from the repository root:

```powershell
python tools/validate_rust_ext.py
```

Equivalent direct commands:

```powershell
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test apps.core apps.tenants apps.identity apps.modules apps.configurations apps.themes apps.audit tests --settings=config.settings.test
```

Local development uses SQLite by default. To point development settings at the Compose PostgreSQL service, start the service and set:

```powershell
$env:DJANGO_DATABASE_ENGINE = "postgres"
python backend/manage.py check
```

The local PostgreSQL defaults match `infra/compose/docker-compose.yml`: database, user, and password all use `mobile_framework`.

Worker settings default to synchronous in-process execution for local validation. Future persistent queue integrations can opt into Redis-compatible settings with:

```powershell
$env:WORKER_BACKEND = "redis"
$env:WORKER_BROKER_URL = "redis://localhost:6379/0"
```

## Planned Areas

- `apps/core`: shared kernel, health checks, event bus, service lifecycle, error model, background job primitives. Initial service lifecycle, event bus, API error model, and job registry baselines exist.
- `apps/tenants`: tenant model and isolation rules. Initial tenant model baseline exists.
- `apps/identity`: users, roles, permissions, sessions, and MFA/OIDC hooks. Initial RBAC model baseline exists.
- `apps/modules`: module manifests, dependency checks, compatibility checks. Initial module registry, dependency validation, and compatibility validation baselines exist.
- `apps/configurations`: tenant-scoped definitions, revisions, status workflow, and schema validation. Initial configuration registry baseline exists.
- `apps/app_builder`: app definitions, navigation, screens, actions, publish states.
- `apps/form_builder`: form definitions, fields, validation, submissions.
- `apps/workflow_builder`: workflow definitions, state machines, tasks, simulation.
- `apps/themes`: design tokens, theme validation, preview, publishing. Initial theme model and revision baseline exists.
- `apps/deployments`: immutable package compilation, signing, channels, rollback.
- `apps/sync`: mobile sync protocol, outbox handling, conflict handling.
- `apps/audit`: mutation logs, config revisions, admin and sync audit events. Initial audit event model baseline exists.
- `rust_ext`: bounded PyO3/maturin helpers. Initial scaffold exists; helper implementations remain pending.
