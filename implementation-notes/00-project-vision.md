# Project Vision

## Product Vision

Create a dynamic, configurable, low-code mobile platform that can support many different use cases without rebuilding the mobile app for every client or workflow.

The platform has three major surfaces:

1. Server-side backend and control plane.
2. Server-side admin frontend for configuring and publishing mobile apps.
3. Client-side mobile runtime that downloads configuration and renders the app dynamically.

The platform should feel modern, approachable, and powerful. Non-technical users should be able to build useful mobile apps through visual builders, while developers can extend the platform through typed modules and plugins.

## Intended Users

### Platform Administrators

They manage tenants, users, permissions, themes, modules, app versions, deployment channels, and mobile sync behavior.

### App Configurators

They use builders to define forms, screens, navigation flows, workflows, rules, data models, and app branding.

### Developers

They build backend modules, frontend builder modules, mobile runtime widgets, integrations, and Rust performance helpers.

### Mobile End Users

They use apps generated/configured by the platform. They may work online or offline.

## What The Platform Must Enable

- Create configurable apps without writing code.
- Configure navigation, screens, forms, lists, actions, workflows, permissions, themes, and offline behavior.
- Publish immutable app configuration packages.
- Let mobile clients download and apply approved configuration packages.
- Support multiple tenants and multiple app versions.
- Keep configuration schema-driven and versioned.
- Support offline-first mobile usage with safe sync.
- Provide extension points similar to openIMIS modules.
- Maintain industry-standard testing, security, code quality, documentation, and release practices.

## What This Platform Is Not

- It is not a generic no-code system that runs arbitrary user code on mobile devices.
- It is not a CMS-only platform.
- It is not just a form builder.
- It is not a mobile app generator that produces a separate custom codebase for every client.

The preferred model is a stable mobile runtime plus dynamic, signed, versioned configuration packages.

## Product Principles

### Configuration Before Custom Code

If a feature can be expressed safely as typed configuration, use configuration. Only use custom code when the platform needs a reusable extension point.

### Schemas Before Screens

Every builder writes to a clear schema. The UI is only one way to edit the schema.

### Runtime Safety

Mobile clients should only execute behavior supported by the shipped runtime. Configuration may select widgets, actions, validation rules, workflows, and data bindings, but should not inject arbitrary code.

### Module Symmetry

Backend, admin frontend, and mobile runtime should all use a similar module concept:

- Backend module contributes models, services, API schema, permissions, jobs, events, and configuration validators.
- Frontend module contributes routes, menu entries, builder panels, translations, and UI extension points.
- Mobile module contributes runtime widgets, actions, screen renderers, sync handlers, and theme mappings.

### Version Everything

Version schemas, modules, app definitions, deployment packages, theme definitions, workflows, APIs, and mobile runtime compatibility.

### Friendly Builder UX

Builder screens should be clear, visual, direct, and safe. They must include previews, validation messages, undo/redo where possible, and accessibility checks.

