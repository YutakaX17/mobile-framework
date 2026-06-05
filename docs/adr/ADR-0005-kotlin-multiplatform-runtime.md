# ADR-0005: Kotlin Multiplatform Mobile Runtime

## Status

Accepted

## Context

The mobile client should be a stable runtime that downloads signed configuration packages and renders supported screens, forms, themes, actions, and sync behavior dynamically. The project should avoid generating a separate custom mobile codebase for every client.

## Decision

Use Kotlin Multiplatform with Compose Multiplatform for the mobile runtime. Shared runtime logic should live in common modules, with platform-specific adapters for secure storage, background work, and native integration.

## Consequences

The runtime can share package parsing, validation, rendering contracts, and sync logic across targets. The runtime must verify packages before applying them, keep the last known good package, and never execute arbitrary downloaded code.
