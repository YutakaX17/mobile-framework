# Codex Working Instructions

These instructions are for Codex when implementing this project inside IntelliJ IDEA Ultimate or another coding surface.

## Global Rules

- Read this folder before implementing.
- Start from architecture and contracts before feature UI.
- Keep changes small and reviewable.
- Prefer existing project patterns once code exists.
- Do not implement arbitrary downloaded code execution.
- Treat schemas as source of truth.
- Update tests with behavior changes.
- Update docs with workflow or API changes.
- Keep commit messages human and normal.

## Preferred Implementation Order

1. Repository foundation.
2. Backend kernel.
3. Shared contracts.
4. Rust extension.
5. Admin frontend shell.
6. Theme Builder.
7. Form Builder.
8. App/Screen Builder.
9. Mobile runtime MVP.
10. Workflow Builder.
11. Deployment and production hardening.

## How To Start A Task

For any task:

1. Read the relevant Markdown files in `implementation-notes`.
2. Find the related GitHub issue or create a clear task note.
3. Inspect existing code.
4. Identify contracts/schemas touched.
5. Implement the smallest complete slice.
6. Add or update tests.
7. Run relevant checks.
8. Summarize what changed and what remains.

## Backend Implementation Guidance

- Use Django for core business flows.
- Keep apps/modules focused.
- Add migrations intentionally.
- Put validation in services/schema validators, not only serializers/forms.
- Enforce tenant and permission checks server-side.
- Audit important writes.
- Return structured errors.
- Use PostgreSQL features where useful, but avoid locking the whole design into JSONB-only data.
- Use Rust extension only for focused helper functions.

## Rust Implementation Guidance

- Rust lives behind Python wrappers.
- Keep Rust APIs narrow.
- Test Rust independently.
- Test Python integration.
- Avoid moving business logic into Rust unless there is a strong reason.
- Document every Rust helper's purpose and inputs/outputs.

## Frontend Implementation Guidance

- Use TypeScript strict mode.
- Use generated types from contracts.
- Use accessible UI components.
- Use clear builder layouts:
  - Left/toolbox or navigation panel.
  - Main canvas/preview.
  - Right properties panel.
  - Top action bar for save/validate/publish.
- Avoid hidden magic in builders.
- Show validation errors close to the affected item.
- Include empty, loading, error, and permission states.
- Keep theme tokens separate from implementation styling.

## Mobile Implementation Guidance

- Build a stable runtime, not generated custom apps.
- Download signed configuration packages.
- Verify package before applying.
- Render only supported widgets/actions.
- Store last known good package.
- Work offline.
- Queue mutations in an outbox.
- Sync in batches.
- Keep sync errors visible and recoverable.

## Schema And Contract Guidance

- Every new config area needs a schema.
- Every schema change needs sample valid and invalid fixtures.
- Generate TypeScript/Kotlin/Python types where possible.
- Keep backward compatibility unless intentionally doing a major version change.
- Add migration notes for schema changes.

## Code Review Guidance

When asked to review code, prioritize:

1. Security bugs.
2. Tenant isolation bugs.
3. Permission bypasses.
4. Data loss risks.
5. Mobile sync corruption risks.
6. Config compatibility breaks.
7. Missing tests.
8. Overly complex implementation.

## Commit Message Guidance

Use conventional, human commit messages.

Examples:

- `feat(core): add module manifest model`
- `feat(theme): validate contrast before publish`
- `fix(forms): preserve field order when editing`
- `test(sync): cover rejected conflict response`
- `docs(runtime): describe package compatibility`

Avoid:

- `AI generated changes`
- `Codex implementation`
- `assistant edits`
- `misc updates`
- `stuff`

## Definition Of Done For Codex

Before saying a task is done:

- Implementation matches requirements.
- Tests are added or updated.
- Relevant checks were run.
- Docs are updated if needed.
- No unrelated files were changed.
- Any unable-to-run checks are clearly stated.

