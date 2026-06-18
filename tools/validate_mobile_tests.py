from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"
SHARED_RUNTIME_MAIN = (
    MOBILE / "shared/src/commonMain/kotlin/org/khodola/mobile/runtime"
)
SHARED_RUNTIME_TEST = (
    MOBILE / "shared/src/commonTest/kotlin/org/khodola/mobile/runtime"
)
COMPOSE_MAIN = (
    MOBILE / "composeApp/src/commonMain/kotlin/org/khodola/mobile/runtime/compose"
)
COMPOSE_TEST = (
    MOBILE / "composeApp/src/commonTest/kotlin/org/khodola/mobile/runtime/compose"
)

EXPECTED_SHARED_RUNTIME_TESTS = {
    "MobileRuntimeMarker.kt": "MobileRuntimeMarkerTest.kt",
    "downloader/PackageDownloader.kt": "downloader/PackageDownloaderTest.kt",
    "form/RuntimeFormRenderer.kt": "form/RuntimeFormRendererTest.kt",
    "navigation/RuntimeNavigationRenderer.kt": "navigation/RuntimeNavigationRendererTest.kt",
    "network/PackageNetworkContracts.kt": "network/PackageNetworkContractsTest.kt",
    "outbox/OfflineOutbox.kt": "outbox/OfflineOutboxTest.kt",
    "screen/RuntimeScreenRenderer.kt": "screen/RuntimeScreenRendererTest.kt",
    "security/SecureTokenStore.kt": "security/SecureTokenStoreTest.kt",
    "serialization/PackageSerialization.kt": "serialization/PackageSerializationTest.kt",
    "storage/PackageLocalStore.kt": "storage/PackageLocalStoreTest.kt",
    "sync/RuntimeSyncEngine.kt": "sync/RuntimeSyncEngineTest.kt",
    "theme/RuntimeThemeMapper.kt": "theme/RuntimeThemeMapperTest.kt",
    "verifier/PackageVerifier.kt": "verifier/PackageVerifierTest.kt",
    "widget/RuntimeWidgetRegistry.kt": "widget/RuntimeWidgetRegistryTest.kt",
}

EXPECTED_COMPOSE_TESTS = {
    "RuntimeShellState.kt": "RuntimeShellStateTest.kt",
}


def require_file(path: Path) -> None:
    if not path.is_file():
        raise AssertionError(f"Missing required mobile test file: {path.relative_to(ROOT)}")


def require_test_annotation(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    if "@Test" not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} must contain at least one @Test")


def require_complete_mapping(source_root: Path, expected_tests: dict[str, str]) -> None:
    source_files = {
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.kt")
    }
    expected_sources = set(expected_tests)
    missing_sources = sorted(source_files - expected_sources)

    if missing_sources:
        formatted = ", ".join(missing_sources)
        raise AssertionError(f"Missing mobile test coverage mapping for: {formatted}")


def require_expected_tests(
    source_root: Path,
    test_root: Path,
    expected_tests: dict[str, str],
    *,
    require_all_sources: bool = True,
) -> None:
    if require_all_sources:
        require_complete_mapping(source_root, expected_tests)

    for source_relative, test_relative in expected_tests.items():
        require_file(source_root / source_relative)
        test_path = test_root / test_relative
        require_file(test_path)
        require_test_annotation(test_path)


def main() -> int:
    require_expected_tests(
        SHARED_RUNTIME_MAIN,
        SHARED_RUNTIME_TEST,
        EXPECTED_SHARED_RUNTIME_TESTS,
    )
    require_expected_tests(
        COMPOSE_MAIN,
        COMPOSE_TEST,
        EXPECTED_COMPOSE_TESTS,
        require_all_sources=False,
    )

    print("Mobile runtime test coverage validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
