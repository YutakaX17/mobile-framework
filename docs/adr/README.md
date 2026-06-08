# Architecture Decision Records

This directory contains accepted architecture decisions for the first platform baseline.

## Review Summary

The initial ADR set was reviewed against the MVP scope, glossary, and implementation roadmap. No ADR needs an owner change before implementation continues.

Follow-up ADRs should be added only when a new decision materially changes platform direction, runtime safety, API shape, data ownership, deployment, or compatibility policy.

## ADR Index

| ADR | Decision Area | Status | MVP Review | Owner Action |
| --- | --- | --- | --- | --- |
| [ADR-0001](ADR-0001-monorepo-structure.md) | Monorepo structure | Accepted | Matches the current multi-surface repository plan. | No owner change needed. |
| [ADR-0002](ADR-0002-django-control-plane.md) | Django control plane | Accepted | Matches backend kernel and tenant/RBAC direction. | No owner change needed. |
| [ADR-0003](ADR-0003-rust-extension-boundary.md) | Rust extension boundary | Accepted | Remains deliberately deferred until a bounded helper need is proven. | No owner change needed. |
| [ADR-0004](ADR-0004-admin-frontend-stack.md) | Admin frontend stack | Accepted | Matches the planned Vite, React, TypeScript admin shell. | No owner change needed. |
| [ADR-0005](ADR-0005-kotlin-multiplatform-runtime.md) | Kotlin Multiplatform runtime | Accepted | Matches the no-downloaded-code mobile runtime constraint. | No owner change needed. |
| [ADR-0006](ADR-0006-configuration-package-model.md) | Configuration package model | Accepted | Matches immutable package and rollback requirements. | No owner change needed. |
| [ADR-0007](ADR-0007-api-split.md) | Admin and mobile API split | Accepted | Matches GraphQL admin and REST mobile/operations separation. | No owner change needed. |
| [ADR-0008](ADR-0008-module-plugin-architecture.md) | Module and plugin architecture | Accepted | Matches manifest-driven extension and compatibility requirements. | No owner change needed. |
| [ADR-0009](ADR-0009-sync-protocol.md) | Mobile sync protocol | Accepted | Matches offline outbox and audit requirements. | No owner change needed. |
| [ADR-0010](ADR-0010-theme-token-model.md) | Theme token model | Accepted | Matches typed theme schema and builder/runtime sharing. | No owner change needed. |

## Open Follow-Ups

These do not block the initial ADR set:

- Add an ADR if the root task runner choice becomes material.
- Add an ADR if repository hosting, branch protection, or release policy creates architecture-level constraints.
- Add an ADR if Rust moves from deferred helper boundary to concrete implementation.
- Add an ADR if mobile sync conflict policy becomes more specific than accept, reject, or manual review.

## Review Rule

Each new ADR should be reviewed before the dependent implementation PR merges. If a decision is superseded, keep the original ADR and add a new ADR that references it.
