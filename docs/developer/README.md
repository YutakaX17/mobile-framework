# Developer Documentation

This area contains setup and workflow guidance for contributors.

## Documents

- [Backend module guide](BACKEND_MODULES.md)
- [Developer getting started](GETTING_STARTED.md)
- [Frontend module guide](FRONTEND_MODULES.md)
- [Local environment setup](LOCAL_SETUP.md)

## Current Baseline

The repository has baseline validation across backend, frontend, mobile, Rust, contracts, docs, CI, security, release, and deployment workflows. Start with the getting started guide, then use the local setup guide for tool-specific details.

Core documentation validation commands:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```
