# ADR-0004: Admin Frontend Stack

## Status

Accepted

## Context

The admin surface needs a modern, type-safe builder UI with routing, server-state management, local builder state, drag/drop, validation, accessibility checks, and previews.

## Decision

Use Vite, React, and TypeScript for the admin frontend. Use TanStack Query for server state and Redux Toolkit for complex local builder/editor state. Keep a platform-specific design system layer above any selected component primitives.

## Consequences

The frontend can be built with strict typing and generated contract types. Builder state remains explicit and inspectable. The team must avoid coupling schema behavior to UI-only assumptions; schemas remain the source of truth.
