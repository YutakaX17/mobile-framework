# Mobile Framework

A server-managed, use-case-agnostic mobile app platform.

The platform will let administrators configure data models, forms, screens, workflows, themes, permissions, and deployments through a web builder. A Kotlin Multiplatform mobile runtime will download signed, versioned configuration packages and render the app dynamically with offline support.

## Current Status

This repository is in foundation setup. Planning lives in `implementation-notes/` and should be read before implementation work starts.

No application features are implemented yet. The first implementation target is the platform kernel: module registry, typed schemas, configuration package versioning, theme tokens, runtime contracts, sync contract, and CI quality gates.

## Repository Areas

- `backend/`: Django control plane and bounded Rust extension integration.
- `frontend-admin/`: Vite, React, and TypeScript admin builder surface.
- `mobile/`: Kotlin Multiplatform and Compose Multiplatform runtime.
- `contracts/`: Shared schemas, API contracts, fixtures, and generated types.
- `infra/`: Local compose, Docker, CI/CD, and observability assets.
- `docs/`: ADRs and project documentation.
- `implementation-notes/`: Working architecture and implementation brief.
- `Notes/`: Reference openIMIS source folders used for analysis.

## Implementation Order

1. Repository foundation.
2. Backend kernel.
3. Shared contracts.
4. Rust extension.
5. Admin frontend shell.
6. Theme Builder.
7. Form Builder.
8. App and Screen Builder.
9. Mobile runtime MVP.
10. Workflow Builder.
11. Deployment and production hardening.

## Development Rule

Do not start by building many features. Build the platform kernel first, keep changes small, and update `implementation-notes/12-project-status.md` when project progress changes.
