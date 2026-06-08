# Contract Tests

Run the full contract validation suite from the repository root:

```powershell
python contracts/validate_contracts.py
```

Install test dependencies if needed:

```powershell
python -m pip install -r contracts/requirements.txt
```

The validation runner checks:

- Every schema listed in `contracts/validation_manifest.json` is a valid Draft 2020-12 schema.
- Every valid fixture passes its schema.
- Every invalid fixture fails its schema.
- Every JSON fixture under `contracts/fixtures/valid` and `contracts/fixtures/invalid` is listed in the manifest.
- The unittest-based contract tests pass.
