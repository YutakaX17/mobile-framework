# CI/CD, Release, And Versioning

## Branching Model

Recommended branches:

- `main`: production-ready code.
- `develop`: integration branch if the team wants one.
- `feature/<short-name>`: normal feature work.
- `fix/<short-name>`: bug fixes.
- `release/<version>`: release stabilization.
- `hotfix/<short-name>`: urgent production fixes.

Small teams can simplify by using trunk-based development with short-lived branches into `main`.

## Pull Request Rules

Every PR should include:

- Clear title.
- Linked issue.
- Scope summary.
- Test evidence.
- Screenshots for UI changes.
- Migration notes for DB changes.
- Security notes for auth, sync, tenant, plugin, or deployment changes.
- Documentation updates where needed.

Avoid commit messages or PR titles that mention AI assistance.

Good examples:

- `feat(backend): add module manifest validation`
- `feat(theme): add contrast validation`
- `test(sync): cover rejected outbox item`
- `docs(adr): record package signing approach`
- `fix(forms): preserve field order after drag`

Avoid:

- `codex changes`
- `ai generated implementation`
- `assistant update`
- `misc fixes`

## GitHub Actions Workflows

Recommended workflows:

### `ci-backend.yml`

Runs:

- Install Python dependencies.
- Run Ruff.
- Run type checks.
- Run pytest.
- Upload coverage.

### `ci-rust.yml`

Runs:

- cargo fmt check.
- cargo clippy.
- cargo test.
- cargo audit.
- maturin build.

### `ci-frontend-admin.yml`

Runs:

- Install Node dependencies.
- TypeScript check.
- ESLint.
- Unit tests.
- Build.

### `ci-mobile.yml`

Runs:

- Gradle checks.
- Kotlin tests.
- SQLDelight migration tests.
- Android build where possible.

### `ci-contracts.yml`

Runs:

- Validate JSON Schemas.
- Validate sample packages.
- Generate types.
- Check generated output is committed or reproducible.
- Run contract tests.

### `ci-e2e.yml`

Runs:

- Start Docker Compose stack.
- Run migrations.
- Seed test data.
- Run Playwright E2E tests.

### `security.yml`

Runs:

- CodeQL.
- Dependency scanning.
- Secret scanning.
- Container scan.
- SBOM generation.

### `release.yml`

Runs:

- Validate version.
- Build backend image.
- Build frontend image.
- Build mobile artifacts for configured channels.
- Generate changelog.
- Generate SBOM.
- Sign images.
- Create GitHub release.
- Deploy to staging.

## Environments

Use separate environment configuration for:

- Local development.
- CI.
- Staging.
- Production.

Do not store secrets in repository files.

Use GitHub Environments for staging and production approvals.

## Docker Deployment Model

Local/dev Compose should include:

- Backend API.
- Backend worker.
- Migration service.
- Admin frontend.
- PostgreSQL.
- Redis or RabbitMQ.
- Object storage emulator if assets are needed.
- Observability tools where useful.

Production should use separate containers/images:

- API.
- Worker.
- Scheduler.
- Admin frontend.
- Migration job.

## Database Migration Rules

- Migrations must be reviewed carefully.
- Destructive migrations require explicit rollout plan.
- Long-running migrations require staged deployment plan.
- Data migrations require tests.
- Releases must run migrations before starting new app version.
- Rollback plan must account for schema changes.

## Versioning

Use Semantic Versioning.

- MAJOR: incompatible API/config/runtime changes.
- MINOR: backward-compatible features.
- PATCH: backward-compatible fixes.

Version these separately:

- Platform backend.
- Admin frontend.
- Mobile runtime.
- Configuration schema.
- Published app packages.
- Plugin API.

## Compatibility Matrix

Maintain a compatibility matrix:

```text
Platform version | Schema version | Mobile runtime min | Mobile runtime max | Plugin API
1.0.x            | 1              | 1.0.0              | 1.x                | 1
```

Mobile clients must refuse packages outside their supported runtime range.

## Release Channels

Support:

- `dev`
- `test`
- `staging`
- `production`

An app package can be active in one or more channels.

## Release Process

1. Merge feature PRs.
2. Update changelog.
3. Bump versions.
4. Create release branch if needed.
5. Run full CI.
6. Build signed artifacts.
7. Deploy to staging.
8. Run E2E tests.
9. Run smoke test on mobile.
10. Promote to production.
11. Monitor logs and metrics.
12. Keep rollback package ready.

## Rollback Process

Backend rollback:

- Prefer forward fixes.
- If rollback is needed, use previous image and confirm database compatibility.

Admin frontend rollback:

- Redeploy previous frontend image.

Mobile app package rollback:

- Activate previous signed package in the deployment channel.
- Mobile clients should fetch the new active manifest and apply the previous package if compatible.

## Changelog

Use Keep a Changelog style:

- Added.
- Changed.
- Deprecated.
- Removed.
- Fixed.
- Security.

Every release should include:

- Platform changes.
- API changes.
- Schema changes.
- Mobile runtime compatibility.
- Migration notes.
- Known issues.

