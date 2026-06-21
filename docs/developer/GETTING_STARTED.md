# Developer Getting Started

This guide is the first stop for contributors working in the mobile framework monorepo. Use it with [local environment setup](LOCAL_SETUP.md), which has tool-specific installation and troubleshooting notes.

## 1. Understand The Repository

Read these files before taking an issue:

- `README.md`: repository purpose, major areas, and validation entry points.
- `implementation-notes/12-project-status.md`: current local progress mirror.
- `implementation-notes/05-github-project-breakdown.md`: epic and task breakdown.
- `docs/site.json`: documentation navigation baseline.
- `.github/workflows/`: CI, security, release, and deployment workflow baselines.

Primary code areas:

- `backend/`: Django control plane and bounded Rust extension integration.
- `frontend-admin/`: Vite, React, and TypeScript admin builder.
- `mobile/`: Kotlin Multiplatform runtime.
- `contracts/`: shared JSON Schemas, fixtures, and generated contract types.
- `tools/`: local validators and artifact generators.
- `docs/`: developer, admin, operations, runtime, plugin, product, and ADR documentation.

## 2. Sync Local State

Start each task from current `main`:

```powershell
git switch main
git pull --ff-only origin main
git status --short --branch
```

If `git status` shows unrelated local changes, do not stage or revert them unless they are part of your task.

## 3. Pick Or Create A Task

Remote GitHub issues are the source of truth. Before creating a new task, search existing issues for the same scope:

```powershell
gh issue list --state all --search "EPIC-13 developer guide"
```

For implementation work, use one branch per issue:

```powershell
git switch -c task/<issue-number>-<short-slug>
```

Branch names should make the issue easy to recognize later, for example `task/291-developer-getting-started-guide`.

## 4. Make A Focused Change

Keep each PR scoped to the task acceptance criteria. Prefer existing patterns over new abstractions, and update the local tracker when task progress changes:

```text
implementation-notes/12-project-status.md
```

For documentation work, also update the relevant section index and any validation script that should enforce the new document.

## 5. Run Local Validation

Use the narrowest relevant checks first, then the broad checks before committing.

Documentation changes:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Contract changes:

```powershell
python contracts/validate_contracts.py
python tools/validate_foundation.py
```

Backend changes:

```powershell
python tools/validate_backend.py
python tools/validate_python.py
```

Mobile runtime changes:

```powershell
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
```

Frontend changes:

```powershell
cd frontend-admin
npm ci
npm run validate
```

Rust extension changes:

```powershell
python tools/validate_rust_ext.py --include-python-wrapper
```

Before a PR, check the final diff:

```powershell
git diff --check
git status --short
```

## 6. Commit And Open A PR

Stage only files that belong to the task:

```powershell
git add <paths>
git commit -m "<concise task summary>"
git push -u origin <branch-name>
```

Open the PR with:

- Summary of user-visible or maintainer-visible changes.
- Validation commands that passed.
- `Closes #<task-issue-number>`.
- `Updates #<parent-epic-number>` when the task advances an epic.

## 7. After Merge

After a PR is green and merged:

```powershell
git switch main
git pull --ff-only origin main
git status --short --branch
```

Confirm the task issue closed and review the next open task before continuing.

## Working Rules

- Keep secrets out of the repository.
- Keep generated build outputs out of commits unless the task explicitly requires committed generated artifacts.
- Prefer small PRs tied to one issue.
- Keep docs and validators aligned with behavior changes.
- Do not revert unrelated local changes.
