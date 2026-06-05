# Mobile Runtime

Kotlin Multiplatform and Compose Multiplatform runtime for rendering signed configuration packages.

## Planned Areas

- `shared`: runtime kernel, package verifier, schemas, sync engine, local store abstractions.
- `composeApp`: shared Compose UI and dynamic renderers.
- `androidApp`: Android entry point and platform adapters.
- `iosApp`: iOS entry point and platform adapters.
- `desktopApp`: optional desktop preview/runtime target.

The runtime must never execute arbitrary downloaded code. It should render only widgets, actions, and workflows supported by the shipped runtime.
