# Rust Extension

Bounded PyO3/maturin helpers for backend package and configuration operations.

Rust code in this directory must stay narrow and independently tested. Keep ordinary Django CRUD, admin workflows, and business logic in Python unless measurement or implementation complexity justifies a Rust helper.

## Layout

- `Cargo.toml`: Rust crate metadata.
- `pyproject.toml`: maturin build metadata.
- `src/lib.rs`: native extension entry point.
- `python/mobile_framework_rust`: Python wrapper package.

## Local Checks

Run Rust tests from the repository root:

```powershell
python tools/validate_rust_ext.py
```

The validation script runs `cargo fmt --check` and `cargo test` against this crate.

To also build the Python package and run wrapper tests:

```powershell
python tools/validate_rust_ext.py --include-python-wrapper
```

Build the Python extension for local development after installing maturin:

```powershell
python -m pip install maturin
python -m maturin develop --manifest-path backend/rust_ext/Cargo.toml
```

## Helpers

- `health_check()`: confirms the native module is importable.
- `extension_version()`: returns the Rust crate version.
- `canonicalize_json(input)`: parses JSON and returns deterministic minified JSON with object keys ordered recursively. Invalid JSON returns an error instead of panicking.
- `diff_app_json(old_input, new_input)`: compares two app definition JSON payloads and returns a deterministic JSON array of changes with `change_type`, `path`, and `old`/`new` values where applicable.
- `hash_config_json(input)`: canonicalizes JSON and returns a stable `sha256:<hex>` digest for configuration payloads.
- `hash_package_json(input)`: canonicalizes JSON and returns a stable `sha256:<hex>` digest for deployment package payloads.
- `merge_sync_json(base_input, local_input, remote_input)`: performs a deterministic three-way JSON merge and returns `{"status":"merged"|"conflict","merged":...,"conflicts":[...]}`. Conflicts include stable `path`, `base`, `local`, and `remote` values.

Package signing and sync endpoint/model work should be added in separate tracked tasks.
