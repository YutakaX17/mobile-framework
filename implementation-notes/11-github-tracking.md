# GitHub Repo And Project Tracking

## Current Status

The local planning files are ready for a GitHub repository.

Repository creation still requires one of these:

- GitHub CLI installed and authenticated locally.
- A blank GitHub repository created manually by the owner.
- A GitHub connector/tool that exposes repository creation.

The connected GitHub app can list repositories and create issues/files in existing repositories, but the exposed tools in this environment do not include creating a new repository or creating a GitHub Project board.

## Recommended Repository

Recommended repository name:

```text
mobile-framework
```

Recommended owner:

```text
YutakaX17
```

Recommended visibility:

- Private while the architecture and MVP are being built.
- Public only when licensing, secrets, and contribution model are ready.

## After The Blank Repo Exists

Codex should do the following:

1. Initialize the local workspace as a git repo if it is not already one.
2. Add the GitHub remote.
3. Commit the `implementation-notes` folder and `.github` templates.
4. Push to the default branch.
5. Create GitHub labels from `05-github-project-breakdown.md`.
6. Create milestones from `05-github-project-breakdown.md`.
7. Create epic issues.
8. Create task issues.
9. Create a GitHub Project board.
10. Add all issues to the Project board.

## Suggested Git Commands

Use these only after the GitHub repo exists:

```bash
git init
git branch -M main
git add implementation-notes .github
git commit -m "docs: add implementation planning notes"
git remote add origin https://github.com/YutakaX17/mobile-framework.git
git push -u origin main
```

## Suggested GitHub Project Columns

Use these statuses:

- Backlog
- Ready
- In Progress
- In Review
- Blocked
- Done

## Issue Tracking Rules

Each task issue should have:

- Epic reference.
- Acceptance criteria.
- Required tests.
- Required docs.
- Notes file reference.
- Completion checkbox.

Example:

```markdown
## Goal

Implement the backend module manifest model and validation service.

## Scope

- Add model.
- Add validation.
- Add tests.
- Add docs update.

## Acceptance Criteria

- [ ] Module manifest schema validates enabled modules.
- [ ] Dependency errors are reported clearly.
- [ ] Tests cover valid and invalid manifests.
- [ ] `implementation-notes/12-project-status.md` is updated.

## Notes

See `implementation-notes/02-target-architecture.md` and `implementation-notes/05-github-project-breakdown.md`.
```

## Codex Completion Protocol

When Codex completes a task:

1. Run relevant checks.
2. Update the GitHub issue with a summary if working directly on GitHub.
3. Update `implementation-notes/12-project-status.md`.
4. Use a PR body with `Closes #issue_number`.
5. Do not close the issue until the implementation is merged or the owner explicitly asks to close it.

## Repo Creation Blocker Note

If Codex cannot create the repository because no repo-creation tool or authenticated GitHub CLI is available, it should stop and ask the owner to create a blank repo or install/authenticate GitHub CLI.
