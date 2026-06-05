# Implementation Roadmap

This roadmap is designed for Codex and human contributors to implement in safe, reviewable increments.

## Phase 0: Decisions And Repository Foundation

Goal: create a clean project base before writing platform features.

Tasks:

- Create monorepo structure.
- Add `README.md`, `LICENSE`, `.editorconfig`, `.gitignore`, and contribution docs.
- Add ADR folder and first ADRs:
  - Monorepo decision.
  - Django plus Rust extension decision.
  - Vite plus React admin decision.
  - Kotlin Multiplatform mobile decision.
  - Configuration package model decision.
  - GraphQL/REST API split decision.
- Add GitHub issue templates.
- Add pull request template.
- Add CODEOWNERS.
- Add branch protection requirements.
- Add initial Docker Compose skeleton.

Exit criteria:

- Repository opens cleanly in IntelliJ IDEA Ultimate.
- Basic docs explain how the project is organized.
- CI can run a placeholder validation workflow.

## Phase 1: Backend Kernel

Goal: establish the control plane foundation.

Tasks:

- Scaffold Django project under `backend`.
- Add PostgreSQL settings.
- Add environment settings with dev/test/prod separation.
- Add core module.
- Add tenant model.
- Add user/role/permission model or integrate Django auth with platform permissions.
- Add module manifest model and loader.
- Add typed module metadata.
- Add configuration registry model.
- Add configuration revision model.
- Add audit event model.
- Add health check endpoints.
- Add base service lifecycle:
  - Validate.
  - Before event.
  - Execute.
  - After event.
  - Audit/log.
- Add background worker setup.

Exit criteria:

- Backend boots.
- Database migrations run.
- Tests cover core module registry and configuration validation.

## Phase 2: Rust Extension Kernel

Goal: add PyO3/maturin integration without overusing Rust.

Tasks:

- Create `backend/rust_ext`.
- Configure maturin.
- Add Python package wrapper.
- Add Rust functions for:
  - JSON canonicalization.
  - Config hash generation.
  - Package hash generation.
  - App definition diff.
  - Basic merge helper.
- Add Rust unit tests.
- Add Python integration tests.
- Add CI job for Cargo fmt, clippy, test, and maturin build.

Exit criteria:

- Django can import the Rust extension.
- CI builds and tests the extension.

## Phase 3: Shared Contracts

Goal: make schemas the source of truth.

Tasks:

- Create `contracts/schemas`.
- Define schema for:
  - Module manifest.
  - App definition.
  - Screen definition.
  - Component definition.
  - Action definition.
  - Form definition.
  - Field definition.
  - Workflow definition.
  - Theme definition.
  - Sync rule definition.
  - Deployment package.
- Add schema validation tests.
- Add type generation for:
  - Python.
  - TypeScript.
  - Kotlin.
- Add compatibility matrix document.

Exit criteria:

- A sample app package validates.
- Generated types are available to backend, frontend, and mobile.

## Phase 4: Admin Frontend Shell

Goal: build the frontend control surface foundation.

Tasks:

- Scaffold Vite + React + TypeScript app.
- Add routing.
- Add auth shell.
- Add API client.
- Add module contribution registry.
- Add design system foundation.
- Add global layout:
  - Sidebar/topbar.
  - Workspace area.
  - Notifications.
  - User menu.
- Add route guards and permission guards.
- Add common states:
  - Loading.
  - Empty.
  - Error.
  - Unauthorized.
  - Validation summary.

Exit criteria:

- Admin frontend can log in against backend dev auth.
- Module routes can be registered through contribution metadata.

## Phase 5: Theme Builder

Goal: implement first visual builder because theme tokens affect both admin and mobile.

Tasks:

- Define theme schema.
- Implement theme list.
- Implement theme editor.
- Add color token editor.
- Add typography token editor.
- Add spacing/shape controls.
- Add logo asset support.
- Add live preview.
- Add contrast checks.
- Add save draft, validate, publish.
- Add mobile theme mapper contract.

Exit criteria:

- A theme can be created, validated, published, and included in an app package.

## Phase 6: Form Builder

Goal: implement typed dynamic forms.

Tasks:

- Define form schema.
- Implement form list.
- Implement drag/drop builder.
- Implement field properties panel.
- Implement validation rule editor.
- Implement conditional visibility editor.
- Implement preview.
- Implement backend form definition APIs.
- Implement form submission APIs.
- Add tests for schema validation and rendering.

Exit criteria:

- A form can be created, previewed, published, rendered, and submitted.

## Phase 7: App And Screen Builder

Goal: assemble full mobile app structure.

Tasks:

- Define app/navigation/screen schemas.
- Implement app list.
- Implement app editor.
- Implement navigation builder.
- Implement screen canvas.
- Implement component toolbox.
- Implement properties panel.
- Implement action binding.
- Implement permissions binding.
- Implement preview with selected theme.

Exit criteria:

- A complete app with navigation, screens, forms, and theme can be published as a package.

## Phase 8: Mobile Runtime MVP

Goal: render published packages on mobile.

Tasks:

- Scaffold Kotlin Multiplatform project.
- Add Compose Multiplatform shared UI.
- Add package manifest downloader.
- Add signature/hash verification.
- Add local package storage.
- Add theme mapper.
- Add navigation renderer.
- Add screen renderer.
- Add basic widget registry.
- Add form renderer.
- Add SQLite local store.
- Add basic sync outbox.

Exit criteria:

- Mobile app can download a dev package, verify it, render navigation/screens/forms, submit offline, and sync online.

## Phase 9: Workflow Builder And Task Engine

Goal: add workflow and approval capabilities.

Tasks:

- Define workflow schema.
- Add backend task/workflow models.
- Add workflow state-machine validator.
- Add workflow visual editor.
- Add task inbox.
- Add trigger/action handlers.
- Add workflow simulation.
- Add audit and tests.

Exit criteria:

- A form submission can trigger a workflow and create a task assigned to a role/user.

## Phase 10: Production Hardening

Goal: move from MVP to releasable platform.

Tasks:

- Add observability.
- Add structured logging.
- Add metrics.
- Add tracing.
- Add backup/restore docs.
- Add load tests.
- Add security scans.
- Add dependency update automation.
- Add release automation.
- Add staging deployment.
- Add rollback process.

Exit criteria:

- A release candidate can be deployed to staging, tested end-to-end, and promoted or rolled back.

