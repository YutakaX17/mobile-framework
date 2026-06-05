# ADR-0001: Monorepo Structure

## Status

Accepted

## Context

The platform has coordinated backend, admin frontend, mobile runtime, contracts, infrastructure, and documentation surfaces. These parts must evolve together because app packages, schemas, generated types, runtime compatibility, and CI gates cross project boundaries.

## Decision

Use a monorepo with these top-level areas:

- `backend/`
- `frontend-admin/`
- `mobile/`
- `contracts/`
- `infra/`
- `docs/`
- `implementation-notes/`

## Consequences

Shared contracts and generated types can be reviewed in the same pull request as backend, frontend, or mobile changes. CI can enforce cross-surface compatibility. The repository will need clear ownership, focused pull requests, and path-scoped checks to avoid unnecessary build cost.
