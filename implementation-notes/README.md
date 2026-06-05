# Implementation Notes

This folder is the working brief for building the dynamic, configurable, low-code mobile platform.

It exists so that when the `mobile-framework` folder is opened in IntelliJ IDEA Ultimate, Codex and human contributors can understand the intended platform without relying on chat history.

## Reading Order

1. `00-project-vision.md`
2. `01-openimis-analysis.md`
3. `02-target-architecture.md`
4. `03-detailed-requirements.md`
5. `04-implementation-roadmap.md`
6. `05-github-project-breakdown.md`
7. `06-quality-security-testing.md`
8. `07-ci-cd-release-versioning.md`
9. `08-documentation-maintenance.md`
10. `09-codex-working-instructions.md`
11. `10-intellij-setup-and-owner-next-steps.md`
12. `11-github-tracking.md`
13. `12-project-status.md`

## One Sentence Goal

Build a server-managed, use-case-agnostic mobile app platform where administrators can configure data models, forms, screens, workflows, themes, permissions, and deployments through a friendly web builder, while a Kotlin Multiplatform mobile runtime downloads signed configuration packages and renders the app dynamically with offline support.

## Chosen Stack

- Backend control plane: Python Django.
- Backend high-performance extension layer: Rust through PyO3 and maturin.
- Server database: PostgreSQL.
- Admin frontend: Vite, React, TypeScript.
- Mobile client: Kotlin Multiplatform and Compose Multiplatform.
- Mobile offline database: SQLite through SQLDelight or an equivalent multiplatform persistence library.
- Background jobs: Celery/RQ or a Django-compatible task runner, with Redis or RabbitMQ depending on deployment preference.
- Deployment: Docker Compose for local/dev and container images for staging/production.

## Primary Rule

Do not start by building many features. Start by building the platform kernel:

- Module registry.
- Typed configuration schemas.
- App/config package versioning.
- Theme tokens.
- Form/screen runtime contracts.
- Mobile sync contract.
- CI quality gates.

Once those foundations are stable, build the visual builders and runtime modules on top of them.

## Tracking Rule

GitHub Issues and the GitHub Project board are the source of truth once the repository exists. The local `12-project-status.md` file is the IntelliJ/Codex companion tracker and should be updated in the same pull request that completes or materially advances a task.
