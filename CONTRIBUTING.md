# Contributing

Read `implementation-notes/README.md` before starting work.

## Contribution Posture

This repository is currently owner-led. External contributions may be accepted through GitHub pull requests after review.

By submitting a contribution, you agree that your contribution is provided under the Apache License 2.0, the same license as this repository.

No Contributor License Agreement is required at this stage. This can be revisited if the project gains regular external contributors or organization-level governance.

## Working Rules

- Keep changes small and reviewable.
- Link work to a GitHub issue once the repository is connected.
- Treat schemas and contracts as source of truth.
- Update tests with behavior changes.
- Update docs and `implementation-notes/12-project-status.md` when project progress changes.
- Do not add arbitrary downloaded code execution to the mobile runtime.
- Keep tenant isolation, permissions, audit, and compatibility in scope for backend changes.

## Pull Requests

Every PR should include:

- Scope summary.
- Linked issue.
- Test evidence.
- Documentation/status updates where needed.
- Security, tenant, permissions, schema, and runtime compatibility notes where relevant.

Avoid PR titles or commit messages that mention AI assistance.
