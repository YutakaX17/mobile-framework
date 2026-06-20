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
- `[x]` M1 Backend Kernel.
- `[x]` M2 Contracts And Rust Extension.
- `[x]` M3 Admin Shell.
- `[~]` M4 Theme And Form Builder MVP.
- `[~]` M5 Mobile Runtime MVP.
- `[ ]` M6 Workflow And Deployment MVP.
- `[ ]` M7 Production Hardening.

## Epics

- `[x]` EPIC-00 Product And Architecture.
- `[x]` EPIC-01 Repository And Tooling.
- `[x]` EPIC-02 Backend Core.
- `[x]` EPIC-03 Rust Extension.
- `[x]` EPIC-04 Shared Contracts.
- `[x]` EPIC-05 Admin Frontend Shell.
- `[x]` EPIC-06 Theme Builder.
- `[x]` EPIC-07 Form Builder.
- `[x]` EPIC-08 App And Screen Builder.
- `[x]` EPIC-09 Deployment Packages.
- `[x]` EPIC-10 Mobile Runtime.
- `[x]` EPIC-11 Workflow Builder.
- `[~]` EPIC-12 CI/CD, Security, And Release.
- `[ ]` EPIC-13 Documentation And Maintenance.

## Active Work

- `[x]` EPIC-07 Form Builder: form backend model, read-only API, list page, designer toolbox, canvas, properties, conditional logic, validation rule, preview, submission endpoint, and mobile contract baselines are complete.
- `[x]` EPIC-08 App And Screen Builder: app definition model/API, app list page, screen builder canvas, component registry, component property editor, navigation model/schema, screen model/schema, action binding, permission binding, mobile preview, app validation, and publish draft flow baselines are complete.
- `[x]` EPIC-09 Deployment Packages: package model, compiler, signing, hash verification, release channel, activation, rollback, mobile manifest endpoint, package download endpoint, and audit event baselines are complete.
- `[x]` EPIC-10 Mobile Runtime: KMP project scaffold, shared Compose module, networking contract, secure token storage, serialization, local store, package downloader, verifier, theme mapper, navigation renderer, screen renderer, widget registry, form renderer, offline outbox, sync engine, and mobile test coverage baselines are complete.
- `[x]` EPIC-11 Workflow Builder: workflow schema, definition model, state-machine validator, task model, task assignment model, workflow trigger model, visual editor, simulator, task inbox, execution log, and test coverage validation baselines are complete.
- `[~]` EPIC-12 CI/CD, Security, And Release: Python, Rust, frontend lint/test/build, mobile Gradle test, contract test, Playwright E2E, dependency scan, CodeQL, secret scanning, Docker build, SBOM generation, image signing, and staging deployment workflow baselines are complete; release workflow remains pending.
- `[x]` EPIC-06 Theme Builder: theme backend model, read-only API, list page, token detail, contrast checker, live preview, asset reference, publish workflow, rollback workflow, and editing workflow baselines are complete.

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
- `[x]` Task `#70` completed: generated TypeScript contract declarations and freshness check added.
- `[x]` Task `#72` completed: generated Python contract declarations and freshness check added.
- `[x]` Task `#74` completed: generated Kotlin contract declarations and freshness check added.
- `[x]` Task `#76` completed: standalone component schema, fixtures, tests, and generated types added.
- `[x]` Task `#78` completed: workflow schema, fixtures, tests, and generated types added.
- `[x]` Task `#80` completed: sync rule schema, fixtures, tests, and generated types added.
- `[x]` EPIC-04 Shared Contracts completed: schema fixtures, validation, contract workflow, and generated TypeScript/Python/Kotlin outputs are in place.
- `[x]` Task `#83` completed: initial PyO3/maturin Rust extension scaffold added.
- `[x]` Task `#85` completed: Rust JSON canonicalization helper added.
- `[x]` Task `#87` completed: Rust config JSON hash helper added.
- `[x]` Task `#89` completed: Rust package JSON hash helper added.
- `[x]` Task `#91` completed: Rust app definition diff helper added.
- `[x]` Task `#93` completed: Rust sync JSON merge helper added.
- `[x]` Task `#95` completed: Rust extension validation script and CI job added.
- `[x]` Task `#97` completed: Rust extension Python wrapper tests added and wired into CI.
- `[x]` EPIC-03 Rust Extension completed: PyO3/maturin scaffold, bounded JSON helpers, Rust tests, Python wrapper tests, and CI validation are in place.
- `[x]` Task `#100` completed: admin frontend Vite React TypeScript scaffold and validation wiring added.
- `[x]` Task `#102` completed: admin frontend routing foundation added.
- `[x]` Task `#104` completed: admin frontend API client foundation added.
- `[x]` Task `#106` completed: admin frontend auth flow shell added.
- `[x]` Task `#108` completed: admin frontend module contribution registry added.
- `[x]` Task `#110` completed: admin frontend design system foundation added.
- `[x]` Task `#112` completed: admin frontend icon system added.
- `[x]` Task `#114` completed: admin frontend shell layout foundation added.
- `[x]` Task `#116` completed: admin frontend permissions guard added.
- `[x]` Task `#118` completed: admin frontend error boundary added.
- `[x]` Task `#120` completed: admin frontend notification system added.
- `[x]` Task `#122` completed: admin frontend testing setup added.
- `[x]` Task `#124` completed: admin frontend Playwright smoke test added.
- `[x]` EPIC-05 Admin Frontend Shell completed: Vite React TypeScript scaffold, routing, API client, auth shell, module registry, design system, icons, shell layout, permissions guard, error boundary, notifications, testing setup, Playwright smoke test, documentation, and CI validation are in place.
- `[x]` Task `#127` completed: theme backend model baseline added.
- `[x]` Task `#129` completed: theme backend read-only API baseline added.
- `[x]` Task `#131` completed: theme list page added.
- `[x]` Task `#133` completed: theme editor token detail baseline added.
- `[x]` Task `#135` completed: theme color contrast checker added.
- `[x]` Task `#137` completed: theme live preview baseline added.
- `[x]` Task `#139` completed: theme asset reference baseline added.
- `[x]` Task `#141` completed: theme publish workflow baseline added.
- `[x]` Task `#143` completed: theme rollback workflow baseline added.
- `[x]` Task `#145` completed: theme editing workflow baseline added.
- `[x]` Task `#147` completed: form backend model/API baseline added.
- `[x]` Task `#149` completed: form list page added.
- `[x]` Task `#151` completed: form designer toolbox and canvas baseline added.
- `[x]` Task `#153` completed: form properties panel baseline added.
- `[x]` Task `#155` completed: form conditional logic baseline added.
- `[x]` Task `#157` completed: form validation rule baseline added.
- `[x]` Task `#159` completed: form preview baseline added.
- `[x]` Task `#161` completed: form submission endpoint baseline added.
- `[x]` Task `#163` completed: mobile form contract baseline added.
- `[x]` EPIC-07 Form Builder completed: typed form schema, admin builder surfaces, backend APIs, preview, submission endpoint, and mobile submission contract baseline are in place.
- `[x]` Task `#165` completed: app definition model/API baseline added.
- `[x]` Task `#167` completed: app list page added.
- `[x]` Task `#169` completed: app screen builder canvas baseline added.
- `[x]` Task `#171` completed: component registry baseline added.
- `[x]` Task `#173` completed: component property editor baseline added.
- `[x]` Task `#175` completed: navigation model/schema baseline added.
- `[x]` Task `#177` completed: screen model/schema baseline added.
- `[x]` Task `#179` completed: action binding baseline added.
- `[x]` Task `#181` completed: permission binding baseline added.
- `[x]` Task `#183` completed: mobile preview baseline added.
- `[x]` Task `#185` completed: app validation baseline added.
- `[x]` Task `#187` completed: app publish draft flow baseline added.
- `[x]` EPIC-08 App And Screen Builder completed: app definition API, admin app list, screen builder, component registry, property editor, navigation and screen schemas, action and permission bindings, mobile preview, validation, and publish flow baselines are in place.
- `[x]` Task `#189` completed: deployment package model baseline added.
- `[x]` Task `#191` completed: deployment package compiler baseline added.
- `[x]` Task `#193` completed: deployment package signing baseline added.
- `[x]` Task `#195` completed: deployment package hash verification baseline added.
- `[x]` Task `#197` completed: deployment package release channel baseline added.
- `[x]` Task `#199` completed: deployment package activation baseline added.
- `[x]` Task `#201` completed: deployment package rollback baseline added.
- `[x]` Task `#203` completed: mobile package manifest endpoint baseline added.
- `[x]` Task `#205` completed: package download endpoint baseline added.
- `[x]` Task `#207` completed: deployment package audit event baseline added.
- `[x]` EPIC-09 Deployment Packages completed: immutable package model, compiler, signing, hash verification, release channels, activation, rollback, mobile manifest/download endpoints, and audit events are in place.
- `[x]` Task `#209` completed: Kotlin Multiplatform mobile project scaffold baseline added.
- `[x]` Task `#211` completed: shared Compose runtime shell baseline added.
- `[x]` Task `#213` completed: mobile networking contract baseline added.
- `[x]` Task `#215` completed: mobile package serialization baseline added.
- `[x]` Task `#217` completed: mobile local store baseline added.
- `[x]` Task `#219` completed: secure token storage abstraction added.
- `[x]` Task `#221` completed: mobile package downloader baseline added.
- `[x]` Task `#223` completed: mobile package verifier baseline added.
- `[x]` Task `#225` completed: mobile theme mapper baseline added.
- `[x]` Task `#227` completed: mobile navigation renderer baseline added.
- `[x]` Task `#229` completed: mobile screen renderer baseline added.
- `[x]` Task `#231` completed: mobile widget registry baseline added.
- `[x]` Task `#233` completed: mobile form renderer baseline added.
- `[x]` Task `#235` completed: mobile offline outbox baseline added.
- `[x]` Task `#237` completed: mobile sync engine baseline added.
- `[x]` Task `#239` completed: mobile runtime test coverage baseline added.
- `[x]` EPIC-10 Mobile Runtime completed: KMP runtime scaffold, shared Compose shell, package networking/storage/security/download/verification flows, renderers, sync logic, and mobile test coverage validation are in place.
- `[x]` Task `#241` completed: workflow definition model baseline added.
- `[x]` Task `#243` completed: workflow state-machine validator baseline added.
- `[x]` Task `#245` completed: workflow task model baseline added.
- `[x]` Task `#247` completed: workflow task assignment model baseline added.
- `[x]` Task `#249` completed: workflow trigger model baseline added.
- `[x]` Task `#251` completed: visual workflow editor baseline added.
- `[x]` Task `#253` completed: workflow simulator baseline added.
- `[x]` Task `#255` completed: task inbox baseline added.
- `[x]` Task `#257` completed: workflow execution log baseline added.
- `[x]` Task `#259` completed: workflow builder test coverage validation added.
- `[x]` EPIC-11 Workflow Builder completed: workflow schemas, backend task/workflow models, graph validation, admin editor, simulator, task inbox, execution logs, and CI-backed validation are in place.
- `[x]` Task `#261` completed: Python lint/test workflow baseline added.
- `[x]` Task `#263` completed: Rust lint/test workflow baseline added.
- `[x]` Task `#265` completed: frontend lint/test/build workflow baseline added.
- `[x]` Task `#267` completed: mobile Gradle test workflow baseline added.
- `[x]` Task `#269` completed: contract test workflow baseline added.
- `[x]` Task `#271` completed: Playwright E2E workflow baseline added.
- `[x]` Task `#273` completed: dependency scan workflow baseline added.
- `[x]` Task `#275` completed: CodeQL workflow baseline added.
- `[x]` Task `#277` completed: secret scanning workflow baseline added.
- `[x]` Task `#279` completed: Docker build workflow baseline added.
- `[x]` Task `#281` completed: SBOM generation workflow baseline added.
- `[x]` Task `#283` completed: image signing workflow baseline added.
- `[x]` Task `#285` completed: staging deployment workflow baseline added.
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
- `[x]` Task `#56` completed: in-process event bus baseline and tests added.
- `[x]` Task `#58` completed: API error model baseline and tests added.
- `[x]` Task `#60` completed: PostgreSQL settings helper, development opt-in path, and tests added.
- `[x]` Task `#62` completed: background worker settings helper, job registry baseline, and tests added.
- `[x]` Task `#64` completed: module dependency validation service and tests added.
- `[x]` Task `#66` completed: module compatibility validation service and tests added.
- `[x]` Task `#68` completed: initial backend integration tests added and wired into validation.
- `[x]` EPIC-02 Backend Core completed: Django backend kernel baseline is in place with validation coverage.

## Blockers

- Remaining detailed task issues should be created incrementally from `implementation-notes/05-github-project-breakdown.md` when starting each epic or milestone.

## Update Rules

When completing work:

1. Update the matching checkbox.
2. Add the related GitHub issue number when available.
3. Keep this file high-level; detailed task discussion belongs in GitHub issues and PRs.
4. Commit this update with the implementation PR.

