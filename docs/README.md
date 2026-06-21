# Documentation

Project documentation lives here after implementation begins. Planning notes remain in `implementation-notes/`.

## Site Navigation

The lightweight docs site baseline is defined in `docs/site.json`. It records the top-level navigation targets and is validated locally with:

```powershell
python tools/validate_docs_site.py
```

The manifest is intentionally dependency-free until the project needs a rendered docs site generator.

## Areas

- `product`: MVP scope, product boundaries, and glossary.
- `adr`: architecture decision records and ADR review index.
- `developer`: local setup, repository workflow, and module guides.
- `admin`: administrator and builder user guides.
- `mobile-runtime`: mobile runtime behavior, package compatibility, and sync.
- `plugin-sdk`: module/plugin extension documentation.
- `operations`: repository protection, deployment, backup, restore, monitoring, logging, and incident response.
