# ADR-0007: API Split

## Status

Accepted

## Context

Admin builder workflows benefit from flexible queries and rich editing flows. Mobile clients need small, stable, cacheable endpoints that support package download, sync, and predictable offline behavior.

## Decision

Use GraphQL for admin builder workflows where flexible querying is valuable. Use REST for operational endpoints, mobile package manifests/downloads, and mobile sync unless a specific persisted GraphQL use case is justified later.

## Consequences

The admin surface can evolve with builder needs while mobile endpoints stay stable and cacheable. The mobile runtime must not consume the broad admin GraphQL surface. OpenAPI contracts should describe mobile and operational REST endpoints.
