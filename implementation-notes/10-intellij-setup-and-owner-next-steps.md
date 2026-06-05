# IntelliJ Setup And Owner Next Steps

## Should You Use IntelliJ IDEA Ultimate?

Yes. IntelliJ IDEA Ultimate is a strong fit for this project because it can handle a monorepo with Python, Rust, TypeScript, Docker, databases, and Kotlin-related files.

Recommended companion tool:

- Use Android Studio when working deeply with Android emulator, Compose previews, Android signing, or platform-specific mobile debugging.

## Recommended IntelliJ Plugins

Install or enable:

- Python.
- Rust.
- Kotlin Multiplatform.
- Docker.
- Database Tools.
- Markdown.
- GitHub.
- GraphQL if GraphQL is used.
- EnvFile or equivalent environment helper if preferred.

## Project Opening Flow

1. Open the root `mobile-framework` folder.
2. Mark `backend`, `frontend-admin`, `mobile`, `contracts`, `infra`, and `docs` as important project areas.
3. Read `implementation-notes/README.md`.
4. Ask Codex to start with `EPIC-01 Repository And Tooling`.
5. Keep early work focused on scaffolding and contracts.

## Initial Project Creation Recommendation

Start with the monorepo structure first, not with Django or mobile alone.

Suggested first instruction to Codex:

```text
Read implementation-notes. Create the initial monorepo structure for the platform, including backend, frontend-admin, mobile, contracts, infra, and docs folders. Add placeholder READMEs, ADR template, root README, PR template, issue templates, CODEOWNERS placeholder, and an initial Docker Compose placeholder. Do not implement application features yet.
```

Suggested second instruction:

```text
Implement the backend Django kernel skeleton from implementation-notes: settings layout, core app, tenant app, module registry model, configuration registry model, audit event model, and health endpoint. Add tests and keep it minimal.
```

Suggested third instruction:

```text
Add the contracts package with JSON Schemas for module manifest, theme, form, screen, app, workflow, sync rule, and deployment package. Add sample valid and invalid fixtures and schema validation tests.
```

## Your Way Forward

### Step 1: Decide Repository Name And License

Choose:

- Project/repository name.
- License.
- Whether this is private or public.
- Whether modules/plugins will be private, public, or mixed.

### Step 2: Create GitHub Repository

Create a repository and push the initial monorepo structure.

Enable:

- Issues.
- Projects.
- Actions.
- Dependabot.
- Secret scanning if available.
- Branch protection.

### Step 3: Create GitHub Project

Use `05-github-project-breakdown.md` as the source for epics and tasks.

Start with:

- `EPIC-00 Product And Architecture`
- `EPIC-01 Repository And Tooling`
- `EPIC-02 Backend Core`
- `EPIC-04 Shared Contracts`

### Step 4: Implement Foundation

The first implementation target should be a small vertical foundation:

- Backend can boot.
- Postgres can run locally.
- Contracts can validate sample configs.
- Admin frontend shell can load.
- CI can run basic checks.

### Step 5: Build Theme Builder Before Form Builder

Theme Builder should come early because theme tokens affect:

- Admin preview.
- Mobile runtime.
- App package schema.
- Accessibility rules.

### Step 6: Build Form Builder As The First Functional Builder

Form Builder is the best first functional low-code feature because:

- It has a clear schema.
- It has clear UI.
- It has clear mobile rendering.
- It exercises validation, publishing, and offline submission.

### Step 7: Then Build App/Screen Builder

After forms and themes work, add screens and navigation.

### Step 8: Then Build Mobile Runtime MVP

The mobile runtime should first render:

- Navigation.
- Basic screens.
- Basic forms.
- Theme.
- Offline outbox.
- Basic sync.

## Early Risks To Watch

- Trying to build all builders at once.
- Letting JSON configs become untyped blobs.
- Shipping arbitrary downloaded code to mobile clients.
- Delaying sync design until late.
- Delaying permission/tenant checks.
- Using Rust for too much too early.
- Building UI without accessibility and responsive checks.
- Not versioning configuration packages from the beginning.

## Recommended MVP Scope

MVP should include:

- One tenant.
- User login.
- Role/permission basics.
- Theme Builder.
- Form Builder.
- Simple App Builder with navigation and form screen.
- Package publish.
- Mobile runtime package download.
- Mobile form rendering.
- Offline form submission.
- Sync submitted form to backend.
- Audit logs.
- CI quality gates.

Do not include in MVP:

- Plugin marketplace.
- Arbitrary scripting.
- Complex workflow automation.
- Multi-app store deployment automation.
- Advanced analytics.
- Deep integration builder.

Those can come after the platform kernel is proven.

