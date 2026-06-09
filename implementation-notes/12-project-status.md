# Project Status

This file is the local IntelliJ/Codex companion tracker.

GitHub Issues and the GitHub Project board should be the source of truth after the repository exists. This file should mirror high-level progress so Codex can quickly understand what has been started or completed from inside IntelliJ IDEA Ultimate.

## Status Legend

- `[ ]` Not started.
- `[~]` In progress.
- `[x]` Complete.
- `[!]` Blocked.

## Repository And Tracking

- `[x]` GitHub repository created: `YutakaX17/mobile-framework`.
- `[x]` Local workspace initialized as git repository.
- `[x]` GitHub remote added: `https://github.com/YutakaX17/mobile-framework.git`.
- `[x]` Planning notes pushed to GitHub.
- `[x]` GitHub labels created.
- `[x]` GitHub milestones created.
- `[x]` Epic issues created: `#1` through `#14`.
- `[x]` Task issues created: initial batch `#15` through `#26`.
- `[x]` GitHub Project board created: `Mobile Framework`.
- `[x]` Epic issues added to GitHub Project board.

## Milestones

- `[x]` M0 Repository Foundation.
- `[~]` M1 Backend Kernel.
- `[~]` M2 Contracts And Rust Extension.
- `[ ]` M3 Admin Shell.
- `[ ]` M4 Theme And Form Builder MVP.
- `[ ]` M5 Mobile Runtime MVP.
- `[ ]` M6 Workflow And Deployment MVP.
- `[ ]` M7 Production Hardening.

## Epics

- `[x]` EPIC-00 Product And Architecture.
- `[x]` EPIC-01 Repository And Tooling.
- `[~]` EPIC-02 Backend Core.
- `[ ]` EPIC-03 Rust Extension.
- `[~]` EPIC-04 Shared Contracts.
- `[ ]` EPIC-05 Admin Frontend Shell.
- `[ ]` EPIC-06 Theme Builder.
- `[ ]` EPIC-07 Form Builder.
- `[ ]` EPIC-08 App And Screen Builder.
- `[ ]` EPIC-09 Deployment Packages.
- `[ ]` EPIC-10 Mobile Runtime.
- `[ ]` EPIC-11 Workflow Builder.
- `[ ]` EPIC-12 CI/CD, Security, And Release.
- `[ ]` EPIC-13 Documentation And Maintenance.

## Active Work

- `[~]` EPIC-02 Backend Core: Django project scaffold, tenant model baseline, identity/RBAC model baseline, module registry baseline, configuration registry baseline, audit event baseline, and service lifecycle baseline are in place; event bus, API error model, PostgreSQL-specific settings, and background worker setup remain pending.
- `[~]` EPIC-04 Shared Contracts: initial schema/fixture/validation-runner batch is complete; generated types and future schema expansion remain pending.

## Completed Work

- `[x]` Initial implementation notes created in `implementation-notes`.
- `[x]` GitHub tracking notes and templates prepared locally.
- `[x]` Initial monorepo foundation folders and placeholder docs created locally.
- `[x]` Initial ADRs added under `docs/adr`.
- `[x]` GitHub labels and milestones created.
- `[x]` Epic issues `#1` through `#14` created and added to the `Mobile Framework` Project board.
- `[x]` Initial task batch `#15` through `#26` created and added to the `Mobile Framework` Project board.
- `[x]` Task `#21` completed: schema conventions and initial compatibility matrix documented.
- `[x]` Task `#22` completed: module manifest schema, fixtures, and tests added.
- `[x]` Task `#23` completed: theme schema, fixtures, and tests added.
- `[x]` Task `#24` completed: form and field schemas, fixtures, and tests added.
- `[x]` Task `#25` completed: app, screen, action, and deployment package schema skeletons added.
- `[x]` Task `#26` completed: contract validation runner added and wired into CI.
- `[x]` Task `#19` completed: placeholder CI replaced with foundation validation workflow.
- `[x]` Task `#15` completed: MVP scope and glossary documented.
- `[x]` Task `#16` completed: initial ADR set reviewed and finalized.
- `[x]` Task `#20` completed: local environment setup documentation added.
- `[x]` Task `#18` completed: repository protection checklist documented and baseline settings applied.
- `[x]` Task `#17` completed: Apache-2.0 license and owner-led contribution posture applied.
- `[x]` Task `#41` completed: Django backend project scaffold, health endpoint, and backend validation added.
- `[x]` Task `#43` completed: tenant model baseline, migration, and tests added.
- `[x]` Task `#46` completed: identity/RBAC model baseline, migration, and tests added.
- `[x]` Task `#48` completed: module registry baseline, manifest validation service, migration, and tests added.
- `[x]` Task `#50` completed: configuration registry baseline, schema-backed validation service, migration, and tests added.
- `[x]` Task `#52` completed: audit event model baseline, migration, and tests added.
- `[x]` Task `#54` completed: service lifecycle baseline and tests added.

## Blockers

- Remaining detailed task issues should be created incrementally from `implementation-notes/05-github-project-breakdown.md` when starting each epic or milestone.

## Update Rules

When completing work:

1. Update the matching checkbox.
2. Add the related GitHub issue number when available.
3. Keep this file high-level; detailed task discussion belongs in GitHub issues and PRs.
4. Commit this update with the implementation PR.

