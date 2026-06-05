# Contracts

Shared source of truth for schemas, API contracts, fixtures, and generated types.

## Planned Areas

- `schemas`: JSON Schemas for module manifests, app definitions, screens, components, actions, forms, workflows, themes, sync rules, and deployment packages.
- `graphql`: admin GraphQL contracts where used.
- `openapi`: operational, mobile, and integration REST contracts.
- `generated`: generated Python, TypeScript, and Kotlin types.
- `fixtures`: valid and invalid sample packages/configuration for contract tests.

Contracts should be implemented before Rust package helpers and before builder features depend on runtime package shapes.
