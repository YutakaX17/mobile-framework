# Mobile Runtime

Kotlin Multiplatform and Compose Multiplatform runtime for rendering signed configuration packages.

## Current Scaffold

- `settings.gradle.kts`: Gradle project includes shared runtime, shared Compose UI, Android app, and desktop preview modules.
- `shared`: common runtime kernel source set with runtime identity metadata, transport-backed package/sync networking, secure token storage contracts and key-value implementation, package response serialization DTOs, package local store contracts and key-value implementation, verified package downloader orchestration, theme token mapping, navigation graph rendering, screen model rendering, widget/action safety validation, form model rendering, persistent offline outbox state, sync rule planning, backend receipt handling, and a practical runtime session for the Field Ops MVP flow.
- `composeApp`: shared Compose UI module with a testable runtime shell state that can summarize practical package readiness, unsupported states, and marker metadata.
- `androidApp`: Android application entry point using the shared Compose UI.
- `desktopApp`: desktop preview entry point using the shared Compose UI.
- `iosApp`: placeholder for the native iOS entry point.

## Planned Areas

- `shared`: runtime kernel, secure token storage abstractions, package downloader, package verifier, schemas, sync engine, package serialization, and local store abstractions.
- `composeApp`: shared Compose UI and dynamic renderers.
- `androidApp`: Android entry point and platform adapters.
- `iosApp`: iOS entry point and platform adapters.
- `desktopApp`: optional desktop preview/runtime target.

The runtime must never execute arbitrary downloaded code. It should render only widgets, actions, and workflows supported by the shipped runtime.

## Local Validation

See `TESTING.md` for the current mobile runtime coverage baseline.

Run scaffold validation from the repository root:

```powershell
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
```

Full Gradle build/test execution runs in CI through the mobile Gradle test workflow. A local Gradle installation or wrapper is required to run Kotlin tests on a workstation.
