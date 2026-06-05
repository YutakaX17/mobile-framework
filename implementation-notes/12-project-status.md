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
- `[ ]` GitHub labels created.
- `[ ]` GitHub milestones created.
- `[ ]` Epic issues created.
- `[ ]` Task issues created.
- `[ ]` GitHub Project board created.
- `[ ]` Issues added to GitHub Project board.

## Milestones

- `[~]` M0 Repository Foundation.
- `[ ]` M1 Backend Kernel.
- `[ ]` M2 Contracts And Rust Extension.
- `[ ]` M3 Admin Shell.
- `[ ]` M4 Theme And Form Builder MVP.
- `[ ]` M5 Mobile Runtime MVP.
- `[ ]` M6 Workflow And Deployment MVP.
- `[ ]` M7 Production Hardening.

## Epics

- `[~]` EPIC-00 Product And Architecture.
- `[~]` EPIC-01 Repository And Tooling.
- `[ ]` EPIC-02 Backend Core.
- `[ ]` EPIC-03 Rust Extension.
- `[ ]` EPIC-04 Shared Contracts.
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

- `[~]` EPIC-00 Product And Architecture: initial ADRs have been added under `docs/adr`.
- `[~]` EPIC-01 Repository And Tooling: initial monorepo foundation folders and placeholder files have been created locally. Repository is connected and pushed; GitHub backlog setup is next.

## Completed Work

- `[x]` Initial implementation notes created in `implementation-notes`.
- `[x]` GitHub tracking notes and templates prepared locally.
- `[x]` Initial monorepo foundation folders and placeholder docs created locally.
- `[x]` Initial ADRs added under `docs/adr`.

## Blockers

- `[!]` GitHub backlog automation is blocked: the connector can read the repository but issue creation returned `403 Resource not accessible by integration`, and local GitHub CLI (`gh`) is not installed.

## Update Rules

When completing work:

1. Update the matching checkbox.
2. Add the related GitHub issue number when available.
3. Keep this file high-level; detailed task discussion belongs in GitHub issues and PRs.
4. Commit this update with the implementation PR.

