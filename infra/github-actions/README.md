# GitHub Actions

Active workflow files live in `.github/workflows/`.

## Current Workflows

### CI Foundation

File: `.github/workflows/ci-foundation.yml`

Runs on pull requests and pushes to `main`.

Checks:

- Required repository foundation files and directories exist.
- JSON files parse successfully.
- `.gitignore` contains baseline hygiene entries.
- Placeholder CI workflow has been replaced.
- Contract schemas and fixtures validate through `contracts/validate_contracts.py`.

Run the same checks locally from the repository root:

```powershell
python tools/validate_foundation.py
python contracts/validate_contracts.py
```

Future backend, frontend, Rust, mobile, security, E2E, and release workflows should be added as implementation areas are scaffolded.
