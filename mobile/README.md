# Mobile Runtime

Kotlin Multiplatform and Compose Multiplatform runtime for rendering signed configuration packages.

## Current Scaffold

- `settings.gradle.kts`: Gradle project includes shared runtime, shared Compose UI, Android app, and desktop preview modules.
- `shared`: common runtime kernel source set with baseline runtime identity metadata and package networking contracts.
- `composeApp`: shared Compose UI module with a testable runtime shell state and marker screen.
- `androidApp`: Android application entry point using the shared Compose UI.
- `desktopApp`: desktop preview entry point using the shared Compose UI.
- `iosApp`: placeholder for the native iOS entry point.

## Planned Areas

- `shared`: runtime kernel, package verifier, schemas, sync engine, local store abstractions.
- `composeApp`: shared Compose UI and dynamic renderers.
- `androidApp`: Android entry point and platform adapters.
- `iosApp`: iOS entry point and platform adapters.
- `desktopApp`: optional desktop preview/runtime target.

The runtime must never execute arbitrary downloaded code. It should render only widgets, actions, and workflows supported by the shipped runtime.

## Local Validation

Run scaffold validation from the repository root:

```powershell
python tools/validate_mobile.py
```

Gradle build/test execution will be wired into CI in the mobile Gradle test workflow task.
