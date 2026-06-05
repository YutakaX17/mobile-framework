# ADR-0010: Theme Token Model

## Status

Accepted

## Context

Themes must affect admin previews and mobile runtime rendering without exposing raw unsafe styling behavior as the primary configuration mechanism.

## Decision

Represent themes as typed design tokens: colors, typography, spacing, shape/radius, elevation, component tokens, assets, and mode variants. Validate critical accessibility constraints before publication.

## Consequences

Themes can be shared between admin previews and mobile runtime mappings. Builders should expose token controls and contrast checks. Published packages should include validated theme tokens and compatibility metadata.
