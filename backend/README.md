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
- `apps/core.management.commands.seed_demo_mvp`: idempotent local MVP seed command for one demo tenant, admin user, RBAC, release channels, valid builder revisions, and one active dev deployment package.
- `apps/tenants`: initial tenant model baseline.
- `apps/identity`: initial role, permission, and tenant-scoped user assignment baseline.
- `apps/modules`: initial module registry, manifest validation, dependency validation, and compatibility validation baseline.
- `apps/configurations`: initial tenant-scoped configuration definition and revision registry baseline.
- `apps/app_builder`: initial tenant-scoped app definition, revision baseline, shared app schema validation, and read-only API baseline.
- `apps/themes`: initial tenant-scoped theme model, revision baseline, shared theme schema validation, read-only API baseline, draft editing action baseline, publish action baseline, and rollback action baseline.
- `apps/form_builder`: initial tenant-scoped form definition, revision baseline, shared form schema validation, read-only API baseline, and submission endpoint baseline.
- `apps/deployment_packages`: initial tenant-scoped package model, compiler, signing, hash verification, release channel, activation, rollback, mobile manifest endpoint, package download endpoint, and deployment audit event baseline.
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
python backend/manage.py test apps.core apps.tenants apps.identity apps.modules apps.configurations apps.themes apps.form_builder apps.app_builder apps.deployment_packages apps.audit tests --settings=config.settings.test
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

## Local MVP Demo Seed

After applying migrations to a local development database, seed the practical MVP demo path with:

```powershell
python backend/manage.py migrate
python backend/manage.py seed_demo_mvp
```

The command is idempotent and can be run repeatedly. It creates or reuses:

- Tenant `demo`.
- Admin user `demo-admin` with local-only default password `demo-admin-password`.
- Basic admin/configurator/mobile roles and MVP permissions.
- Default release channels: `dev`, `test`, `staging`, and `production`.
- Core module registration from the shared valid fixture.
- Published theme, form, and app revisions from the shared valid fixtures.
- Active signed and hashed dev deployment package `pkg_demo_field_ops_001`.

Override local demo secrets with environment variables when needed:

```powershell
$env:DEMO_MVP_ADMIN_PASSWORD = "<local password>"
$env:DEMO_MVP_SIGNING_KEY = "<local signing key>"
python backend/manage.py seed_demo_mvp
```

The default credentials and HMAC signing key are for local development only. They are not production key-management guidance.

## Planned Areas

- `apps/core`: shared kernel, health checks, event bus, service lifecycle, error model, background job primitives. Initial service lifecycle, event bus, API error model, and job registry baselines exist.
- `apps/tenants`: tenant model and isolation rules. Initial tenant model baseline exists.
- `apps/identity`: users, roles, permissions, sessions, and MFA/OIDC hooks. Initial RBAC model baseline exists.
- `apps/modules`: module manifests, dependency checks, compatibility checks. Initial module registry, dependency validation, and compatibility validation baselines exist.
- `apps/configurations`: tenant-scoped definitions, revisions, status workflow, and schema validation. Initial configuration registry baseline exists.
- `apps/app_builder`: app definitions, navigation, screens, actions, publish states. Initial app model, revision, and read-only API baselines exist.
- `apps/form_builder`: form definitions, fields, validation, submissions. Initial form model, revision, read-only API, and submission endpoint baselines exist.
- `apps/workflow_builder`: workflow definitions, state machines, tasks, simulation. Initial workflow definition model baseline exists.
- `apps/themes`: design tokens, theme validation, preview, publishing. Initial theme model, revision, and read-only API baselines exist.
- `apps/deployment_packages`: immutable package compilation, signing, channels, rollback. Initial package model, compiler, signing, hash verification, release channel, activation, rollback, mobile manifest endpoint, package download endpoint, and deployment audit event baselines exist.
- `apps/sync`: mobile sync protocol, outbox handling, conflict handling.
- `apps/audit`: mutation logs, config revisions, admin and sync audit events. Initial audit event model baseline exists.
- `rust_ext`: bounded PyO3/maturin helpers. Initial scaffold exists; helper implementations remain pending.
