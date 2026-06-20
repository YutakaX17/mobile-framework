# Mobile Runtime Documentation

This area documents the Kotlin Multiplatform mobile runtime.

## Documents

- [Mobile runtime guide](RUNTIME_GUIDE.md)

## Current Baseline

The runtime has shared package contracts, verification, local storage, theme, navigation, screen, widget, form, offline outbox, sync, and Compose shell baselines.

Core validation commands:

```powershell
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
python tools/validate_foundation.py
```
