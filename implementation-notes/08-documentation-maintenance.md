# Documentation And Maintenance

## Documentation Strategy

Documentation must live with the code and evolve with the code.

Use a docs site such as MkDocs Material or Docusaurus once the project grows. Until then, Markdown in `/docs` is enough.

## Required Documentation Areas

### Developer Documentation

Must include:

- Local setup.
- Repository structure.
- Backend module guide.
- Frontend module guide.
- Mobile runtime module guide.
- Rust extension guide.
- Contract/schema guide.
- Testing guide.
- Debugging guide.
- Release guide.

### Admin Documentation

Must include:

- User and role management.
- App Builder guide.
- Form Builder guide.
- Theme Builder guide.
- Workflow Builder guide.
- Deployment Manager guide.
- Package rollback guide.
- Mobile sync troubleshooting.

### Plugin SDK Documentation

Must include:

- Plugin/module manifest.
- Backend extension points.
- Frontend extension points.
- Mobile runtime extension points.
- Version compatibility rules.
- Security rules.
- Publishing process.

### Operations Documentation

Must include:

- Environment variables.
- Docker Compose setup.
- Production deployment.
- Database backup.
- Database restore.
- Monitoring.
- Logging.
- Incident response.
- Security update process.

## ADRs

Use Architecture Decision Records for major decisions.

Initial ADRs:

- Monorepo structure.
- Django as backend control plane.
- Rust through PyO3/maturin.
- Vite + React + TypeScript admin frontend.
- Kotlin Multiplatform mobile runtime.
- Configuration package model.
- API split.
- Sync protocol.
- Theme token model.
- Plugin/module architecture.

ADR format:

```text
# ADR-0001: Title

## Status

Accepted

## Context

What problem are we solving?

## Decision

What did we choose?

## Consequences

What tradeoffs follow?
```

## Maintenance Plan

### Weekly

- Review open PRs.
- Review failing CI.
- Triage bugs.
- Review dependency update PRs.

### Monthly

- Update dependencies.
- Review security scan results.
- Review docs for stale setup steps.
- Review performance dashboards.
- Review sync error reports.

### Per Release

- Update changelog.
- Update compatibility matrix.
- Update docs for new features.
- Write migration notes.
- Confirm rollback plan.
- Tag release.

### Quarterly

- Review architecture debt.
- Review plugin API stability.
- Review mobile runtime compatibility.
- Review backup/restore drill.
- Review threat model.

## Ownership

Each module should have:

- Owner.
- Backup owner.
- Documentation owner.
- Test owner or test responsibility.

Use CODEOWNERS to route reviews.

## Deprecation Policy

When removing or replacing a schema/API/plugin feature:

1. Mark as deprecated in docs.
2. Add warning in validation output if possible.
3. Provide migration path.
4. Keep compatibility for at least one minor release unless security requires faster removal.
5. Remove in next major release.

## Support Policy

Define support windows:

- Current minor release receives features and fixes.
- Previous minor release receives critical fixes.
- Older versions receive security fixes only if explicitly supported.

## Backups And Recovery

Must document:

- PostgreSQL backup schedule.
- Object storage backup schedule.
- Restore procedure.
- Restore testing cadence.
- Recovery time objective.
- Recovery point objective.

## Observability

Track:

- API latency.
- Error rate.
- Worker queue depth.
- Failed jobs.
- Package publication failures.
- Mobile package download failures.
- Sync success/failure counts.
- Conflict counts.
- Login failures.
- Permission denied spikes.

Recommended tools:

- Structured logs.
- Prometheus/Grafana or equivalent.
- Sentry/GlitchTip for frontend and backend exceptions.
- OpenTelemetry when tracing becomes valuable.

