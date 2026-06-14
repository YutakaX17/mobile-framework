# Contracts

Shared source of truth for schemas, API contracts, fixtures, and generated types.

## Planned Areas

- `schemas`: JSON Schemas for module manifests, app definitions, screens, components, actions, forms, workflows, themes, sync rules, and deployment packages.
- `graphql`: admin GraphQL contracts where used.
- `openapi`: operational, mobile, and integration REST contracts.
- `generated`: generated Python, TypeScript, and Kotlin types.
- `fixtures`: valid and invalid sample packages/configuration for contract tests.
- `tests`: unittest-based contract validation tests.

Contracts should be implemented before Rust package helpers and before builder features depend on runtime package shapes.

## Contract Rules

- [Schema conventions](SCHEMA_CONVENTIONS.md)
- [Compatibility matrix](COMPATIBILITY_MATRIX.md)

## Validation Command

Install dependencies if needed:

```powershell
python -m pip install -r contracts/requirements.txt
```

Run the full contract validation suite from the repository root:

```powershell
python contracts/validate_contracts.py
```

Regenerate Kotlin, Python, and TypeScript declarations from the v1 schemas:

```powershell
python contracts/generate_types.py
```

For manifest-driven schema and fixture validation only:

```powershell
python contracts/validate_contracts.py --skip-unittest
```
