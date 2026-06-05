# ADR-0008: Module And Plugin Architecture

## Status

Accepted

## Context

The platform should be extensible like openIMIS, but with stricter typing, compatibility checks, and runtime safety across backend, frontend, and mobile surfaces.

## Decision

Use manifest-driven modules. Backend modules can contribute models, services, API schema, permissions, jobs, events, and configuration validators. Frontend modules can contribute routes, menus, builder panels, translations, guards, and previews. Mobile modules can contribute supported widgets, actions, renderers, sync handlers, and theme mappings.

Module manifests must be typed, versioned, and checked for dependency and platform compatibility.

## Consequences

The platform can grow through reusable modules without arbitrary downloaded code execution. Compatibility checks must happen before startup or package publication. The module registry is part of the platform kernel and should be implemented early.
