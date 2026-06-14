# Generated Types

Generated Python, TypeScript, and Kotlin types live here. Generated output should be reproducible in CI.

## TypeScript

The current TypeScript declarations are generated from the v1 JSON Schemas:

```powershell
python contracts/generate_types.py
```

Contract validation checks that the committed TypeScript output is current:

```powershell
python contracts/generate_types.py --check
python contracts/validate_contracts.py
```
