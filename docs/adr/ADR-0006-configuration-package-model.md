# ADR-0006: Configuration Package Model

## Status

Accepted

## Context

Administrators need to publish app definitions, forms, screens, workflows, themes, permissions, data models, sync rules, and assets to mobile clients safely. Mobile clients need deterministic compatibility and rollback behavior.

## Decision

Use immutable, signed, versioned configuration packages. Publishing creates a new package; rollback activates a previous compatible package instead of editing a published package.

A package must include compatibility metadata, schema version, module list, theme, navigation, screens, forms, workflows, permissions, data models, sync rules, assets, hash, and signature.

## Consequences

Package history remains auditable and mobile clients can refuse incompatible packages. Package compilation must be transactional. Schema changes need compatibility rules, fixtures, generated types, and migration notes.
