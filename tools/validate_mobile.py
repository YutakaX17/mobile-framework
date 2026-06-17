from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"

REQUIRED_FILES = [
    "settings.gradle.kts",
    "build.gradle.kts",
    "gradle.properties",
    "gradle/libs.versions.toml",
    "shared/build.gradle.kts",
    "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/MobileRuntimeMarker.kt",
    "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/downloader/PackageDownloader.kt",
    "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/network/PackageNetworkContracts.kt",
    "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/security/SecureTokenStore.kt",
    "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/serialization/PackageSerialization.kt",
    "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/storage/PackageLocalStore.kt",
    "shared/src/commonTest/kotlin/org/khodola/mobile/runtime/MobileRuntimeMarkerTest.kt",
    "shared/src/commonTest/kotlin/org/khodola/mobile/runtime/downloader/PackageDownloaderTest.kt",
    "shared/src/commonTest/kotlin/org/khodola/mobile/runtime/network/PackageNetworkContractsTest.kt",
    "shared/src/commonTest/kotlin/org/khodola/mobile/runtime/security/SecureTokenStoreTest.kt",
    "shared/src/commonTest/kotlin/org/khodola/mobile/runtime/serialization/PackageSerializationTest.kt",
    "shared/src/commonTest/kotlin/org/khodola/mobile/runtime/storage/PackageLocalStoreTest.kt",
    "composeApp/build.gradle.kts",
    "composeApp/src/commonMain/kotlin/org/khodola/mobile/runtime/compose/MobileRuntimeApp.kt",
    "composeApp/src/commonMain/kotlin/org/khodola/mobile/runtime/compose/RuntimeShellState.kt",
    "composeApp/src/commonTest/kotlin/org/khodola/mobile/runtime/compose/RuntimeShellStateTest.kt",
    "androidApp/build.gradle.kts",
    "androidApp/src/main/AndroidManifest.xml",
    "androidApp/src/main/kotlin/org/khodola/mobile/runtime/android/MainActivity.kt",
    "androidApp/src/main/res/values/styles.xml",
    "desktopApp/build.gradle.kts",
    "desktopApp/src/main/kotlin/org/khodola/mobile/runtime/desktop/Main.kt",
    "iosApp/README.md",
]

EXPECTED_SETTINGS_ENTRIES = [
    'include(":shared")',
    'include(":composeApp")',
    'include(":androidApp")',
    'include(":desktopApp")',
]


def require_file(path: Path) -> None:
    if not path.is_file():
        raise AssertionError(f"Missing required mobile scaffold file: {path.relative_to(ROOT)}")


def require_contains(path: Path, expected: str) -> None:
    content = path.read_text(encoding="utf-8")
    if expected not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} must contain `{expected}`")


def main() -> int:
    for relative_path in REQUIRED_FILES:
        require_file(MOBILE / relative_path)

    settings = MOBILE / "settings.gradle.kts"
    for expected in EXPECTED_SETTINGS_ENTRIES:
        require_contains(settings, expected)

    version_catalog = MOBILE / "gradle/libs.versions.toml"
    require_contains(version_catalog, 'kotlin = "2.4.0"')
    require_contains(version_catalog, 'compose = "1.11.1"')
    require_contains(version_catalog, 'agp = "9.2.0"')
    require_contains(version_catalog, 'serialization = "1.11.0"')

    require_contains(
        MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/MobileRuntimeMarker.kt",
        'supportedSchemaVersion = "v1"',
    )
    require_contains(
        MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/downloader/PackageDownloader.kt",
        "interface MobilePackageDownloader",
    )
    require_contains(
        MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/network/PackageNetworkContracts.kt",
        "interface MobileRuntimeNetworkClient",
    )
    require_contains(
        MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/security/SecureTokenStore.kt",
        "interface MobileSecureTokenStore",
    )
    require_contains(
        MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/serialization/PackageSerialization.kt",
        "fun decodePackageManifestResponse",
    )
    require_contains(
        MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime/storage/PackageLocalStore.kt",
        "interface MobilePackageLocalStore",
    )
    require_contains(
        MOBILE / "composeApp/src/commonMain/kotlin/org/khodola/mobile/runtime/compose/MobileRuntimeApp.kt",
        "fun MobileRuntimeApp",
    )
    require_contains(
        MOBILE / "composeApp/src/commonMain/kotlin/org/khodola/mobile/runtime/compose/RuntimeShellState.kt",
        "data class RuntimeShellState",
    )

    print("Mobile scaffold validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
