# ADR-0003: Rust Extension Boundary

## Status

Accepted

## Context

Some platform operations may become CPU-heavy or security-sensitive, such as canonicalizing JSON, hashing packages, diffing app definitions, validating large configuration payloads, or helping sync conflict resolution.

## Decision

Use Rust through PyO3 and maturin only for bounded helpers with clear inputs and outputs. Do not use Rust for ordinary CRUD, admin workflows, or business logic until measurement or complexity justifies it.

## Consequences

The backend remains productive in Django while Rust can improve selected hot paths. Rust APIs must stay narrow, independently tested, and covered by Python integration tests. Shared contracts should be stabilized before implementing Rust package helpers.
