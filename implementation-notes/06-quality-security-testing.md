# Quality, Security, And Testing

## Quality Philosophy

Quality should be automatic first and human-reviewed second.

Every pull request should answer:

- Is the design appropriate?
- Is the behavior correct?
- Is it tested at the right level?
- Is it secure?
- Is it understandable?
- Does it preserve compatibility?
- Does it update documentation where needed?

## Backend Quality

Use:

- Ruff for linting and formatting.
- Pyright or mypy for type checking.
- pytest for tests.
- pytest-django for Django tests.
- factory_boy or model_bakery for test data.
- coverage for coverage reporting.
- bandit for Python security checks.
- pip-audit or safety for dependency checks.

Backend test types:

- Unit tests for services and validators.
- Model tests for constraints and lifecycle behavior.
- API tests for GraphQL/REST endpoints.
- Permission tests for every protected operation.
- Migration tests for important data migrations.
- Contract tests for schema behavior.
- Integration tests with PostgreSQL.

## Rust Quality

Use:

- cargo fmt.
- cargo clippy.
- cargo test.
- cargo audit.
- criterion for benchmarks where needed.
- maturin build test.

Rust test types:

- Unit tests for each helper.
- Property-style tests for diff/merge where useful.
- Python integration tests for PyO3 wrappers.
- Benchmarks only for code that is performance-sensitive.

## Admin Frontend Quality

Use:

- TypeScript strict mode.
- ESLint.
- Prettier.
- Vitest.
- React Testing Library.
- Playwright.
- Axe accessibility checks.
- Storybook or a local component preview system if useful.

Frontend test types:

- Unit tests for pure helpers.
- Component tests for builders and property panels.
- Integration tests for save/validate/publish flows.
- Accessibility checks for key builder screens.
- Playwright E2E tests for core workflows.
- Visual smoke tests for layout stability.

## Mobile Quality

Use:

- Kotlin test.
- Compose UI tests.
- SQLDelight migration tests.
- Ktor client tests with mock engine.
- Android instrumentation tests.
- iOS smoke tests where CI capacity allows.

Mobile test types:

- Package verification tests.
- Theme mapping tests.
- Screen rendering tests.
- Form rendering tests.
- Offline outbox tests.
- Sync protocol tests.
- Conflict resolution tests.
- App startup smoke tests.

## Contract Testing

Contract tests are mandatory because backend, frontend, and mobile share configuration schemas.

Contract tests must verify:

- Every sample app package validates.
- Invalid packages fail with useful errors.
- Generated TypeScript types match schemas.
- Generated Kotlin types match schemas.
- Backend APIs accept and return expected shapes.
- Mobile runtime can parse the active package schema version.

## Security Requirements

### Authentication

- Use secure password hashing.
- Support MFA-ready architecture.
- Rotate session/token secrets safely.
- Store mobile tokens securely.
- Rate-limit login and sensitive endpoints.

### Authorization

- Enforce permissions on every endpoint.
- Enforce tenant scope on every query and mutation.
- Test negative permission cases.
- Avoid relying only on frontend guards.

### Input Validation

- Validate all configuration against JSON Schema.
- Validate all API inputs.
- Sanitize user-provided content.
- Prevent injection vulnerabilities.
- Limit upload size and file types.

### Output And Browser Security

- Use secure headers.
- Use CSRF protection where cookies are used.
- Use CORS allowlists.
- Avoid unsafe HTML rendering.
- Use Content Security Policy.

### Mobile Security

- Use HTTPS only.
- Verify package signatures.
- Do not execute downloaded code.
- Keep sensitive local data protected.
- Support remote package deactivation.
- Support forced update if runtime is unsafe.

### Supply Chain

- Use dependency scanning.
- Use lockfiles.
- Generate SBOMs for releases.
- Sign container images.
- Pin critical build dependencies where appropriate.

## CI Quality Gates

Pull requests should block merge unless:

- Backend lint passes.
- Backend tests pass.
- Rust fmt/clippy/tests pass.
- Frontend lint/typecheck/tests pass.
- Mobile tests pass for changed mobile code.
- Contract tests pass.
- Security scans pass or have documented accepted risk.
- Build succeeds.

## Code Review Checklist

Reviewers should check:

- Scope is small and coherent.
- Code matches the existing architecture.
- Names are clear.
- Tests cover the risk.
- Errors are structured and user-friendly.
- Permissions are enforced server-side.
- Tenant isolation is preserved.
- Configuration schemas are updated.
- Generated types are refreshed.
- Documentation is updated.
- Migration and rollback implications are clear.

## Code Analysis Process

Codex or a reviewer should analyze changes in this order:

1. Read the issue and acceptance criteria.
2. Inspect touched files.
3. Check related schemas/contracts.
4. Check security and tenant boundaries.
5. Check tests.
6. Run relevant test commands.
7. Review for simplification.
8. Summarize risks and residual gaps.

## Definition Of Done

A task is done when:

- It satisfies acceptance criteria.
- Tests are added or intentionally not needed with explanation.
- Quality checks pass.
- Docs are updated if behavior changed.
- Security and permissions are considered.
- The implementation is reviewable in a small PR.

