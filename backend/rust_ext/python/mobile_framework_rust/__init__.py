"""Python wrapper for bounded Rust backend helpers."""

try:
    from ._native import (
        canonicalize_json,
        extension_version,
        hash_config_json,
        hash_package_json,
        health_check,
    )
except ImportError as exc:  # pragma: no cover - exercised once the extension is built.
    raise ImportError(
        "mobile_framework_rust native extension is not built. "
        "Install it with `python -m maturin develop --manifest-path backend/rust_ext/Cargo.toml`."
    ) from exc

__all__ = [
    "canonicalize_json",
    "extension_version",
    "hash_config_json",
    "hash_package_json",
    "health_check",
]
