# ADR-0009: Mobile Sync Protocol

## Status

Accepted

## Context

Mobile users may work offline. The platform must preserve local changes, sync safely, detect conflicts, and make troubleshooting possible.

## Decision

Use an explicit sync protocol with device registration, active package manifest download, reference/data pull by cursor, local outbox push in batches, server-side validation, per-change accept/reject/conflict results, and sync audit logs.

## Consequences

The mobile runtime can remain offline-first and recoverable. The backend must model sync metadata, outbox results, conflicts, and audit events from the beginning. Sync contracts should be defined before deep mobile implementation.
