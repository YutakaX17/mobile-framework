# Changelog Process

This guide describes how to maintain `CHANGELOG.md` for the mobile framework. It keeps release notes consistent with the release manifest, compatibility matrix, and pull request workflow.

## Current Baseline

The repository keeps a root changelog at:

```text
CHANGELOG.md
```

The changelog starts with an `Unreleased` section. Release-specific sections should be added when versioned releases begin.

Use these categories:

- `Added`;
- `Changed`;
- `Deprecated`;
- `Removed`;
- `Fixed`;
- `Security`.

Use `None.` when a category intentionally has no entries yet. Remove `None.` when adding the first real entry for that category.

## What Needs A Changelog Entry

Add a changelog entry for user-visible, operator-visible, or compatibility-relevant changes.

Examples:

- new backend API behavior;
- admin frontend workflow changes;
- mobile runtime behavior changes;
- contract or schema changes;
- deployment package format changes;
- security fixes;
- migration requirements;
- release process changes;
- deprecations or removals.

Routine internal refactors, test-only changes, and documentation-only wording fixes usually do not need changelog entries unless they affect operators or release process behavior.

## Pull Request Expectations

Every PR should state changelog impact in the PR body.

Use one of:

- `Added CHANGELOG entry`;
- `No changelog entry needed`;
- `Deferred to release PR`.

If a PR changes schema, API, runtime, deployment, plugin, or operational behavior, prefer adding the changelog entry in the same PR. Deferring is acceptable only when a release PR is collecting multiple coordinated entries.

## Entry Style

Write entries as concise past-tense bullets.

Good examples:

- Added deployment package rollback guidance.
- Changed form preview validation wording.
- Fixed mobile package hash verification for signed payloads.
- Documented schema compatibility requirements for platform upgrades.

Avoid:

- vague entries such as `Misc fixes`;
- implementation-only details that do not help users or operators;
- references to AI assistance;
- duplicate entries for the same behavior change.

Include issue or PR references when they help trace a release note:

```text
- Added backup and restore guidance for PostgreSQL environments. (#314)
```

## Release Section Process

When preparing a versioned release:

1. Confirm all merged PRs since the previous release have changelog impact recorded.
2. Group unreleased entries by category.
3. Add a release heading using the release version and date.
4. Move relevant entries from `Unreleased` to the release heading.
5. Reset `Unreleased` categories to `None.`.
6. Update `contracts/COMPATIBILITY_MATRIX.md` when compatibility changed.
7. Generate the release manifest.
8. Include migration notes and known issues in the release entry when applicable.

Suggested release heading format:

```text
## [0.1.0] - 2026-06-21
```

Use the actual release date in `YYYY-MM-DD` format.

## Compatibility Notes

Changelog entries should call out compatibility changes clearly.

Include explicit notes when a release changes:

- schema version;
- deployment package shape;
- mobile runtime minimum or maximum version;
- plugin API compatibility;
- database migration requirements;
- rollback limitations.

The compatibility matrix remains the source of truth for supported platform, schema, mobile runtime, and plugin API combinations. The changelog should summarize what changed and link readers to the matrix when compatibility is affected.

## Security Notes

Use the `Security` category for:

- vulnerability fixes;
- dependency updates that remediate vulnerabilities;
- permission model changes;
- authentication or authorization changes;
- secret handling changes;
- tenant isolation fixes.

Do not include exploit details that would create unnecessary risk before users have time to upgrade.

## Validation

Documentation-only changes to this guide or `CHANGELOG.md` should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Release process changes should also run:

```powershell
python tools/generate_release_manifest.py --version 0.1.0
```
