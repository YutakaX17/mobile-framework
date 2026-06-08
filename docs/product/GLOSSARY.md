# Glossary

This glossary defines project terms used across implementation notes, issues, contracts, code, and documentation.

## Core Product Terms

### Admin Frontend

The web application used by administrators and app configurators to manage tenants, users, roles, themes, forms, apps, deployment packages, and operational state.

### App Builder

The admin frontend area for defining apps, navigation, screens, components, action bindings, permissions, and package-ready app structure.

### App Configurator

A user who configures forms, themes, screens, navigation, and publishable app packages without writing code.

### App Definition

The versioned configuration object that describes an app's navigation, screens, permissions, theme reference, and runtime structure.

### Builder

A visual admin tool that edits typed configuration. The builder UI is not the source of truth; the schema-backed configuration is.

### Configuration Package

An immutable, signed, versioned bundle downloaded by the mobile runtime. It contains app structure, theme, forms, permissions, modules, compatibility metadata, assets, hash, and signature.

### Contract

A schema or API definition shared across backend, admin frontend, mobile runtime, and supporting tools.

### Control Plane

The backend and admin systems responsible for storing, validating, publishing, auditing, and serving configuration packages and operational data.

### Deployment Channel

A named package activation target such as `dev`, `test`, `staging`, or `production`.

### Form Builder

The admin frontend area for defining typed dynamic forms, fields, validation rules, conditional visibility, and submission behavior.

### Last Known Good Package

The most recent package that a mobile runtime verified and applied successfully. The runtime should continue using it when a newer package fails validation or compatibility checks.

### Mobile Runtime

The Kotlin Multiplatform application that downloads, verifies, stores, and renders configuration packages. It renders only supported widgets and actions shipped with the runtime.

### Module

A backend, frontend, and/or mobile extension unit with typed manifest metadata, dependency requirements, compatibility constraints, permissions, and contributed runtime capabilities.

### Package Activation

The operation that marks a published package as active for a release channel. Activation does not mutate the package contents.

### Platform Administrator

A user who manages tenants, users, roles, permissions, release channels, modules, package activation, and operational settings.

### Published Package

An immutable package that has passed validation and has a hash/signature. Published packages are not edited after publication.

### Theme Builder

The admin frontend area for defining design tokens, theme modes, brand assets, preview behavior, and accessibility validation.

## Architecture Terms

### ADR

Architecture Decision Record. A short document that captures a major architectural decision, its context, and consequences.

### Compatibility Matrix

A table that maps platform versions, schema versions, mobile runtime ranges, and plugin API versions.

### Configuration Registry

Backend storage for typed configuration definitions, revisions, validation state, and publish lifecycle state.

### Contract Validation

Automated validation that schemas are well-formed, valid fixtures pass, invalid fixtures fail, and all fixtures are covered by the validation manifest.

### Generated Types

Python, TypeScript, or Kotlin types generated from shared contracts. These are planned after the initial schema set stabilizes.

### JSON Schema

The schema language used for typed configuration contracts.

### Plugin API

The formal extension contract for modules/plugins. It starts at version `0` until extension points are stable.

### Runtime Safety

The rule that package configuration may select supported runtime behavior but must not inject arbitrary code.

### Schema Version

The major version folder for contracts, such as `v1`. Breaking schema changes require a new major schema version.

## Backend Terms

### Audit Event

A structured record of an important action, such as configuration change, publish, activation, role change, sync rejection, or integration call.

### Background Worker

A separate process for asynchronous jobs such as package compilation, sync processing, notifications, or integration retries.

### Django App

A backend module/package unit inside the Django control plane.

### Module Manifest

A typed document declaring module identity, version, dependencies, compatibility, surfaces, permissions, and contributed schemas.

### Tenant

An isolated customer or operational boundary. MVP may expose one tenant, but data models and APIs should still be tenant-scoped.

## Mobile And Sync Terms

### Conflict

A sync condition where the server cannot safely accept a client change without policy or user/operator resolution.

### Device Registration

The process by which a mobile runtime identifies a device to the backend before package download and sync.

### Offline Outbox

Local mobile storage for user actions or submissions created while offline or before successful sync.

### Sync Cursor

A marker used by the mobile runtime and backend to transfer incremental changes.

### Sync Session

A single pull or push interaction between a mobile client and backend, recorded for troubleshooting and audit.

## Security Terms

### Hash

A deterministic digest of package contents used to detect accidental or malicious changes.

### Signature

A cryptographic proof that a package was produced by a trusted publisher. The initial contract includes the field; implementation details come later.

### Tenant Isolation

The requirement that one tenant's users and data cannot access another tenant's records or packages.
