# Mobile Runtime Guide

This guide describes the current Kotlin Multiplatform mobile runtime baseline. It is for contributors working on package download, verification, local storage, rendering, offline outbox, and sync behavior.

## Runtime Layout

The mobile workspace lives under `mobile/` and is split into these Gradle modules:

- `shared`: dependency-light runtime contracts and package-processing logic.
- `composeApp`: shared Compose shell and shell state.
- `androidApp`: Android entry point and platform packaging.
- `desktopApp`: desktop entry point for local runtime inspection.
- `iosApp`: iOS placeholder and integration notes.

The Gradle root is `mobile/settings.gradle.kts`. Keep module names stable because validation and CI expect these exact entries:

```text
include(":shared")
include(":composeApp")
include(":androidApp")
include(":desktopApp")
```

## Shared Runtime Areas

Shared runtime code lives in:

```text
mobile/shared/src/commonMain/kotlin/org/khodola/mobile/runtime/
```

Current runtime areas:

- `MobileRuntimeMarker.kt`: schema compatibility marker.
- `network/PackageNetworkContracts.kt`: package manifest and download network contracts.
- `downloader/PackageDownloader.kt`: package fetch orchestration boundary.
- `verifier/PackageVerifier.kt`: package digest and signature verification boundary.
- `serialization/PackageSerialization.kt`: package payload decoding helpers.
- `storage/PackageLocalStore.kt`: local package persistence boundary.
- `theme/RuntimeThemeMapper.kt`: runtime theme decoding and mapping.
- `navigation/RuntimeNavigationRenderer.kt`: navigation graph decoding.
- `screen/RuntimeScreenRenderer.kt`: screen payload decoding.
- `widget/RuntimeWidgetRegistry.kt`: widget contribution lookup.
- `form/RuntimeFormRenderer.kt`: runtime form payload decoding.
- `outbox/OfflineOutbox.kt`: offline mutation queue contracts.
- `sync/RuntimeSyncEngine.kt`: sync cycle orchestration boundary.

Keep shared code platform-neutral unless a platform-specific API is required. Platform-specific implementations should live behind interfaces declared in `shared`.

## Package Lifecycle

The runtime package lifecycle is:

1. Request package metadata through the network contract.
2. Download the selected package bytes.
3. Verify digest and signing metadata.
4. Decode manifest and package payloads.
5. Store the accepted package locally.
6. Map package content into theme, navigation, screen, widget, and form runtime structures.
7. Render through the Compose shell.
8. Queue offline writes through the outbox when the device is offline.
9. Sync queued writes when network and auth state allow it.

Do not render unverified package content. Verification must complete before local activation.

## Compatibility

The runtime currently supports schema version `v1` through `MobileRuntimeMarker`.

Compatibility rules:

- Reject packages with unsupported `schema_version`.
- Reject packages below the runtime minimum version.
- Reject packages above the runtime maximum version unless the runtime explicitly supports that range.
- Keep compatibility updates aligned with `contracts/COMPATIBILITY_MATRIX.md`.
- Add tests before widening compatibility ranges.

## Rendering Boundaries

Runtime rendering is split by concern:

- Theme mapping turns package theme tokens into runtime-safe style data.
- Navigation rendering decodes route and graph structure.
- Screen rendering decodes screen layout payloads.
- Widget registry resolves component types to runtime renderers.
- Form rendering decodes form schemas and submission metadata.
- Compose shell state tracks active package and runtime shell status.

Avoid coupling package decoding directly to platform entry points. Keep platform apps thin and move shared behavior into `shared` or `composeApp`.

## Offline And Sync

Offline support is intentionally explicit:

- `OfflineOutboxStore` owns persisted queued writes.
- Outbox entries should be deterministic, replayable, and auditable.
- `RuntimeSyncEngine` coordinates upload, retry, and conflict handling.
- Sync should not bypass package compatibility checks.
- Failed sync attempts should preserve enough context for future troubleshooting docs.

When adding outbox or sync behavior, cover success, retry, invalid payload, and conflict cases.

## Security Boundaries

Security-sensitive runtime behavior should stay behind small interfaces:

- token persistence belongs behind `MobileSecureTokenStore`;
- package trust belongs behind `MobilePackageVerifier`;
- package fetching belongs behind `MobileRuntimeNetworkClient`;
- local package activation belongs behind `MobilePackageLocalStore`.

Do not store secrets in package payloads, test fixtures, or committed local state.

## Validation Commands

Run these for mobile runtime changes:

```powershell
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
python tools/validate_foundation.py
```

Run Gradle tests from `mobile/` when the local toolchain is available:

```powershell
cd mobile
gradle :shared:desktopTest :composeApp:desktopTest --stacktrace
```

For documentation-only changes to this guide:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

## Test Expectations

Every shared runtime source file should have a corresponding common test unless the validation mapping intentionally exempts it. The current coverage mapping is enforced by:

```text
tools/validate_mobile_tests.py
```

Expected coverage for runtime changes:

- package manifest and payload decoding;
- package download contract behavior;
- package verification success and failure;
- local package storage behavior;
- theme, navigation, screen, widget, and form decoding;
- offline outbox enqueue and replay rules;
- sync success, retry, and conflict handling;
- Compose shell state transitions.

Prefer small common tests for pure runtime behavior before adding platform-specific tests.

## Platform App Boundaries

Platform apps should stay thin:

- `androidApp` owns Android activity and Android-specific packaging.
- `desktopApp` owns the desktop entry point for inspection.
- `iosApp` remains a placeholder until iOS integration is expanded.

Shared behavior should not be duplicated across platform apps. Add expect/actual declarations only when an interface cannot remain pure common code.
