# Generated Types

Generated Python, TypeScript, and Kotlin types live here. Generated output should be reproducible in CI.

## Python And TypeScript

The current Python and TypeScript declarations are generated from the v1 JSON Schemas:

```powershell
python contracts/generate_types.py
```

Target a single language when needed:

```powershell
python contracts/generate_types.py --target python
python contracts/generate_types.py --target typescript
```

Contract validation checks that the committed generated output is current:

```powershell
python contracts/generate_types.py --check
python contracts/validate_contracts.py
```
