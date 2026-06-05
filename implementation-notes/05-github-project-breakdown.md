# GitHub Project Breakdown

Create a GitHub Project with epics, milestones, and tasks similar to the structure below.

## Tracking Contract For Codex

Once the GitHub repository exists, Codex should treat this file as the backlog source of truth.

For each implementation task:

1. Find or create the matching GitHub issue.
2. Work on a branch linked to that issue.
3. Keep the issue open until acceptance criteria pass.
4. Update `implementation-notes/12-project-status.md` in the same pull request.
5. Close the issue only when the task is genuinely complete.

Each issue should include:

- Goal.
- Scope.
- Acceptance criteria.
- Relevant notes file links.
- Test expectations.
- Documentation expectations.

Recommended issue title format:

```text
[EPIC-02] Add backend module registry
[EPIC-04] Define theme schema
[EPIC-10] Add mobile package verifier
```

Recommended completion marker in PR body:

```text
Closes #123
Updates implementation-notes/12-project-status.md
```

## Labels

Recommended labels:

- `type:epic`
- `type:feature`
- `type:bug`
- `type:task`
- `type:docs`
- `type:test`
- `type:security`
- `type:refactor`
- `area:backend`
- `area:rust`
- `area:frontend-admin`
- `area:mobile`
- `area:contracts`
- `area:infra`
- `area:docs`
- `priority:p0`
- `priority:p1`
- `priority:p2`
- `status:blocked`
- `good-first-task`

## Milestones

1. `M0 Repository Foundation`
2. `M1 Backend Kernel`
3. `M2 Contracts And Rust Extension`
4. `M3 Admin Shell`
5. `M4 Theme And Form Builder MVP`
6. `M5 Mobile Runtime MVP`
7. `M6 Workflow And Deployment MVP`
8. `M7 Production Hardening`

## EPIC-00: Product And Architecture

Goal: define the architecture clearly before implementation expands.

Tasks:

- Write ADR for monorepo structure.
- Write ADR for Django control plane.
- Write ADR for PyO3/maturin Rust extension.
- Write ADR for admin API shape.
- Write ADR for mobile package and runtime model.
- Write ADR for sync protocol.
- Write ADR for module/plugin architecture.
- Write ADR for theme token architecture.
- Define initial personas.
- Define MVP scope.
- Define out-of-scope items.
- Define glossary.

## EPIC-01: Repository And Tooling

Goal: create a productive baseline.

Tasks:

- Create backend folder.
- Create frontend-admin folder.
- Create mobile folder.
- Create contracts folder.
- Create infra folder.
- Create docs folder.
- Add root README.
- Add contribution guide.
- Add PR template.
- Add issue templates.
- Add CODEOWNERS.
- Add editor settings.
- Add root task runner decision.
- Add local environment documentation.

## EPIC-02: Backend Core

Goal: implement Django kernel.

Tasks:

- Scaffold Django project.
- Add settings modules for dev/test/prod.
- Add PostgreSQL connection.
- Add tenant model.
- Add identity/RBAC models.
- Add module manifest model.
- Add module dependency validation.
- Add module compatibility validation.
- Add configuration registry.
- Add configuration revision model.
- Add audit event model.
- Add event bus.
- Add service lifecycle base class.
- Add API error model.
- Add health check endpoint.
- Add background worker configuration.
- Add backend unit tests.
- Add backend integration tests.

## EPIC-03: Rust Extension

Goal: use Rust for bounded performance-sensitive helpers.

Tasks:

- Add maturin project.
- Add PyO3 crate setup.
- Add Python wrapper package.
- Add JSON canonicalization helper.
- Add config hash helper.
- Add package hash helper.
- Add schema validation helper if useful.
- Add app definition diff helper.
- Add sync merge helper.
- Add Cargo tests.
- Add Python wrapper tests.
- Add CI job.

## EPIC-04: Shared Contracts

Goal: make schema-driven development real.

Tasks:

- Add JSON Schema folder.
- Add module manifest schema.
- Add app schema.
- Add screen schema.
- Add component schema.
- Add action schema.
- Add form schema.
- Add field schema.
- Add workflow schema.
- Add theme schema.
- Add sync schema.
- Add package schema.
- Add schema test fixtures.
- Add generated TypeScript types.
- Add generated Python types.
- Add generated Kotlin types.
- Add contract test workflow.

## EPIC-05: Admin Frontend Shell

Goal: establish modern builder shell.

Tasks:

- Scaffold Vite + React + TypeScript.
- Add routing.
- Add API client.
- Add auth flow.
- Add module contribution registry.
- Add design system foundation.
- Add icon system.
- Add shell layout.
- Add permissions guard.
- Add error boundary.
- Add toast/notification system.
- Add testing setup.
- Add Playwright smoke test.

## EPIC-06: Theme Builder

Goal: create first end-to-end builder.

Tasks:

- Add theme backend model/API.
- Add theme schema validation.
- Add theme list page.
- Add theme editor page.
- Add token editor panels.
- Add color contrast checker.
- Add live preview.
- Add logo asset support.
- Add publish workflow.
- Add rollback support.
- Add frontend tests.
- Add backend tests.

## EPIC-07: Form Builder

Goal: create typed form builder and renderer.

Tasks:

- Add form backend model/API.
- Add form schema validation.
- Add form list page.
- Add form designer toolbox.
- Add form canvas.
- Add form properties panel.
- Add conditional logic editor.
- Add validation rule editor.
- Add form preview.
- Add form submission endpoint.
- Add mobile form contract.
- Add tests.

## EPIC-08: App And Screen Builder

Goal: build mobile app composition.

Tasks:

- Add app definition model/API.
- Add navigation model/schema.
- Add screen model/schema.
- Add component registry.
- Add screen builder canvas.
- Add component property editors.
- Add action binding.
- Add permission binding.
- Add mobile preview.
- Add app validation.
- Add app publish draft flow.

## EPIC-09: Deployment Packages

Goal: publish immutable mobile configuration packages.

Tasks:

- Add package model.
- Add package compiler.
- Add package signing.
- Add package hash verification.
- Add release channels.
- Add package activation.
- Add rollback.
- Add mobile package manifest endpoint.
- Add package download endpoint.
- Add audit events.
- Add tests.

## EPIC-10: Mobile Runtime

Goal: render packages in Kotlin Multiplatform.

Tasks:

- Scaffold KMP project.
- Add shared Compose module.
- Add networking.
- Add serialization.
- Add local SQLite store.
- Add secure token storage abstraction.
- Add package downloader.
- Add signature verifier.
- Add theme mapper.
- Add navigation renderer.
- Add screen renderer.
- Add widget registry.
- Add form renderer.
- Add offline outbox.
- Add sync engine.
- Add mobile tests.

## EPIC-11: Workflow Builder

Goal: enable tasks, approvals, and automation.

Tasks:

- Add workflow schema.
- Add workflow definition model.
- Add state machine validator.
- Add task model.
- Add task assignment model.
- Add workflow trigger model.
- Add visual workflow editor.
- Add workflow simulator.
- Add task inbox.
- Add workflow execution logs.
- Add tests.

## EPIC-12: CI/CD, Security, And Release

Goal: ship safely.

Tasks:

- Add Python lint/test workflow.
- Add Rust lint/test workflow.
- Add frontend lint/test/build workflow.
- Add mobile Gradle test workflow.
- Add contract test workflow.
- Add Playwright E2E workflow.
- Add dependency scan workflow.
- Add CodeQL.
- Add secret scanning.
- Add Docker build workflow.
- Add SBOM generation.
- Add image signing.
- Add staging deployment workflow.
- Add release workflow.

## EPIC-13: Documentation And Maintenance

Goal: keep the platform understandable and maintainable.

Tasks:

- Add docs site.
- Add developer getting started guide.
- Add backend module guide.
- Add frontend module guide.
- Add mobile runtime guide.
- Add plugin SDK guide.
- Add admin user guide.
- Add theme builder guide.
- Add form builder guide.
- Add workflow builder guide.
- Add deployment guide.
- Add backup/restore guide.
- Add upgrade guide.
- Add changelog process.
