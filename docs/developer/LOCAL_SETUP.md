# Local Environment Setup

This guide describes the expected local development environment for the monorepo.

The project is still in foundation setup, so some tools are expectations for upcoming scaffolds rather than active build requirements today.

## Required Today

Install these before working on the current repository:

- Git for source control.
- GitHub CLI for issue, pull request, and project-board operations.
- Python 3 with `jsonschema` and Django backend dependencies available for validation.
- A code editor or IDE that can handle Markdown, Python, JSON Schema, TypeScript, Rust, Kotlin, and Docker files.

Recommended IDE:

- IntelliJ IDEA Ultimate for the monorepo.
- Android Studio when working deeply on Android emulator, Compose previews, Android signing, or mobile debugging.

## Expected Later

These tools are not all required by the current foundation checks, but the roadmap expects them:

- Docker Desktop or compatible Docker runtime for local services.
- Node.js LTS and a package manager for the Vite React admin frontend.
- Rust toolchain for bounded PyO3/maturin helpers.
- Java Development Kit for Kotlin Multiplatform tooling.
- Android Studio and Android SDK for Android mobile runtime work.
- PostgreSQL client tooling for backend database inspection.

## Repository Setup

Clone the repository:

```powershell
git clone https://github.com/YutakaX17/mobile-framework.git
cd mobile-framework
```

Confirm GitHub CLI authentication:

```powershell
gh auth status
```

If `gh` is not on `PATH` in PowerShell, use the installed executable path directly:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' auth status
```

## Python Validation Setup

Install the contract validation dependency if needed:

```powershell
python -m pip install jsonschema
```

Install backend dependencies if needed:

```powershell
python -m pip install -r backend/requirements.txt
```

Run the current foundation checks from the repository root:

```powershell
python tools/validate_foundation.py
python contracts/validate_contracts.py
python tools/validate_backend.py
```

Expected result:

- Foundation validation passes.
- Contract validation reports the schema, fixture, and unit test counts.
- Backend validation runs Django system checks, migration checks, PostgreSQL and worker settings tests, core health endpoint, service lifecycle, event bus, API error model, and background job registry tests, tenant model tests, identity/RBAC model tests, module registry and dependency validation tests, configuration registry tests, and audit event model tests.

## Local PostgreSQL

The backend defaults to SQLite for quick local validation. To use the Compose PostgreSQL service instead:

```powershell
docker compose -f infra/compose/docker-compose.yml up -d postgres
$env:DJANGO_DATABASE_ENGINE = "postgres"
python backend/manage.py check
```

The development defaults match Compose:

- `POSTGRES_DB=mobile_framework`
- `POSTGRES_USER=mobile_framework`
- `POSTGRES_PASSWORD=mobile_framework`
- `POSTGRES_HOST=localhost`
- `POSTGRES_PORT=5432`

Production-like settings require explicit `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `DJANGO_SECRET_KEY`. Optional PostgreSQL settings include `POSTGRES_CONN_MAX_AGE` and `POSTGRES_SSLMODE`.

## Worker Settings

Background worker settings are dependency-free for the current baseline. Defaults are safe for local validation:

- `WORKER_BACKEND=sync`
- `WORKER_BROKER_URL=redis://localhost:6379/0`
- `WORKER_QUEUES=default`
- `WORKER_CONCURRENCY=1`
- `WORKER_POLL_INTERVAL_SECONDS=5`

Redis-backed settings can be configured later without changing application code:

```powershell
$env:WORKER_BACKEND = "redis"
$env:WORKER_BROKER_URL = "redis://localhost:6379/0"
$env:WORKER_QUEUES = "default,packages,sync"
```

## Repository Workflow

Use one small branch per issue:

```powershell
git switch main
git pull --ff-only origin main
git switch -c task/<issue-number>-<short-slug>
```

Before committing:

```powershell
python tools/validate_foundation.py
python contracts/validate_contracts.py
python tools/validate_backend.py
git diff --check
git status --short
```

Open pull requests with:

- A concise scope summary.
- Validation commands that passed.
- `Closes #<issue-number>`.
- `Updates implementation-notes/12-project-status.md` when progress changed.

After squash-merging a PR:

```powershell
git switch main
git pull --ff-only origin main
git branch -d task/<issue-number>-<short-slug>
```

Git may warn when deleting a squash-merged branch because the original branch commit is not the same object as the squash commit on `main`. That is expected when the PR is already merged.

## GitHub Project Workflow

Use the `Mobile Framework` GitHub Project as the source of truth.

Typical task status flow:

- `Ready`
- `In Progress`
- `In Review`
- `Done`

Use `Blocked` only when the task needs an owner decision or external prerequisite.

## Current Validation Commands

Run these before every PR until more surface-specific checks are added:

```powershell
python tools/validate_foundation.py
python contracts/validate_contracts.py
python tools/validate_backend.py
git diff --check
```

When frontend, mobile, and Rust scaffolds are added, their setup and test commands should be documented here before or with the first related implementation PR.

## Environment Notes

- Keep secrets out of the repository.
- Use local `.env` files only when the relevant scaffold defines examples and loading rules.
- Do not commit generated caches, virtual environments, build outputs, or IDE-local state.
- Keep JSON Schemas and fixtures deterministic so validation works in CI and local development.

## Troubleshooting

If `gh` is authenticated but PowerShell cannot find it, use:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe'
```

If contract validation fails because `jsonschema` is missing:

```powershell
python -m pip install jsonschema
```

If Git shows line-ending warnings on Windows, treat them as informational unless `git diff --check` reports whitespace errors.
