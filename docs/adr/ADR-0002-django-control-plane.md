# ADR-0002: Django Control Plane

## Status

Accepted

## Context

The backend needs admin workflows, database-backed business models, authentication, authorization, migrations, background jobs, audit trails, and productive module development.

## Decision

Use Django as the backend control plane. Keep core business workflows in Python and Django apps. Use PostgreSQL as the server source of truth.

## Consequences

Django provides strong productivity for admin and control-plane features. The project must enforce typed schemas, structured errors, tenant isolation, and permission checks explicitly. JSONB should be used for flexible configuration, not as a replacement for core relational models.
