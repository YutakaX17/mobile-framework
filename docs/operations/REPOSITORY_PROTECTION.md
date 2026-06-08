# Repository Protection Checklist

This document records the baseline GitHub repository settings for `YutakaX17/mobile-framework`.

## Applied Settings

These settings have been applied to the repository:

| Area | Setting | State |
| --- | --- | --- |
| Repository | Default branch | `main` |
| Repository | Issues | Enabled |
| Repository | Projects | Enabled |
| Repository | Merge commits | Disabled |
| Repository | Rebase merges | Disabled |
| Repository | Squash merges | Enabled |
| Repository | Delete head branches after merge | Enabled |
| Actions | GitHub Actions | Enabled |
| Security | Secret scanning | Enabled |
| Security | Secret scanning push protection | Enabled |
| Security | Dependabot alerts | Enabled |
| Security | Dependabot security updates | Enabled |
| Dependabot | GitHub Actions update schedule | Weekly, Monday 08:00 Africa/Johannesburg |
| Branch protection | `main` branch protection | Enabled |
| Branch protection | Require branches to be up to date before merge | Enabled |
| Branch protection | Required checks | `Validate Foundation`, `GitGuardian Security Checks` |
| Branch protection | Required linear history | Enabled |
| Branch protection | Require conversation resolution | Enabled |
| Branch protection | Allow force pushes | Disabled |
| Branch protection | Allow deletions | Disabled |

## Current Branch Protection Notes

The initial branch protection rule intentionally does not require approving reviews yet.

Reason:

- The repository is currently owner-driven.
- Requiring external approval too early can block foundation work when no reviewer pool exists.
- Pull requests are still used for all task work.
- Required CI/security checks protect `main` before merges.

When additional maintainers exist, update `main` protection to require at least one approving review and CODEOWNERS review for sensitive paths.

## Required Checks

The protected `main` branch requires:

- `Validate Foundation`
- `GitGuardian Security Checks`

`Validate Foundation` currently runs:

```powershell
python tools/validate_foundation.py
python contracts/validate_contracts.py
```

As backend, frontend, mobile, and Rust scaffolds are added, extend CI and then update the required check list if new workflows become merge blockers.

## Dependabot

Tracked configuration:

- `.github/dependabot.yml`

Current scheduled updates:

- GitHub Actions workflow dependencies.

Add more package ecosystems when their manifests exist:

- Python package manifests for backend/tooling.
- npm manifests for `frontend-admin`.
- Cargo manifests for Rust helpers.
- Gradle/Kotlin manifests for `mobile`.

## Owner Follow-Ups

These items require owner judgment and are not forced by this baseline:

- Choose the repository license and contribution posture in task `#17`.
- Decide when review approval should become mandatory.
- Decide whether to disable repository wiki/downloads/discussions if they are not used.
- Decide whether to require signed commits after the contributor model is clear.
- Decide whether to enable auto-merge after branch protection is stable.

## Verification Commands

Repository settings can be checked with GitHub CLI:

```powershell
& 'C:\Program Files\GitHub CLI\gh.exe' api repos/YutakaX17/mobile-framework/branches/main/protection
& 'C:\Program Files\GitHub CLI\gh.exe' api repos/YutakaX17/mobile-framework/actions/permissions
& 'C:\Program Files\GitHub CLI\gh.exe' api repos/YutakaX17/mobile-framework --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge,delete_branch_on_merge,security_and_analysis}'
```
