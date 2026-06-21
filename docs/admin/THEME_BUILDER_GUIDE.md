# Theme Builder Guide

This guide describes the current theme builder baseline for administrators and builders. It focuses on the implemented theme library and detail surfaces, plus the backend draft, publish, and rollback behavior.

## Access

The Themes module is available to users with `themes:manage` or `platform-admin`.

Routes:

- `/themes`: theme library.
- `/themes/:themeId`: theme detail and token inspection.

If the route shows an unauthorized state, confirm the user has the `builder` role or another role that grants `themes:manage`.

## Theme Library

The theme library lists tenant-scoped themes returned by the admin API.

Use the library to review:

- theme identifier;
- theme name and description;
- current revision status;
- current revision version;
- published theme count;
- total theme count.

The Refresh action reloads the theme list. Empty and unavailable states are explicit so administrators can distinguish "no themes exist" from "themes could not load."

## Theme Detail

The theme detail view shows the current revision payload for a selected theme.

Current detail panels:

- live preview;
- assets;
- colors;
- typography;
- spacing;
- radius;
- modes;
- contrast.

If no payload is available, the detail view shows a no-payload state instead of rendering partial token data.

## Token Groups

Theme payloads are schema-backed configuration packages. Important groups:

- `colors`: simple color tokens or color scales with `main`, `light`, `dark`, and `contrast` values.
- `typography`: font family, fallback family, and scale entries.
- `spacing`: numeric spacing tokens rendered as pixel values.
- `radius`: numeric border radius tokens rendered as pixel values.
- `assets`: logo and icon asset references.
- `modes`: named mode overrides such as light or dark display modes.

Keep token names stable. Mobile packages and admin previews may depend on the same token keys.

## Live Preview

The live preview resolves a small set of runtime tokens:

- background;
- surface;
- text;
- primary color;
- button text;
- font family;
- border radius;
- padding.

Mode selection applies `color_overrides` before falling back to base tokens. If a value is missing, the preview uses safe defaults so the panel remains renderable while still making incomplete payloads visible in token panels.

## Contrast Checks

The contrast panel evaluates:

- color scales that provide both `main` and `contrast` values;
- modes that provide both `text` and `background` overrides.

Ratios are shown in `x.xx:1` format. Status labels:

- `AAA`: ratio is at least 7:1.
- `AA`: ratio is at least 4.5:1.
- `Fail`: ratio is below 4.5:1 or cannot satisfy AA.

Invalid hex values are ignored by contrast calculations. Fix invalid colors in the theme payload before publishing.

## Draft Updates

The backend supports draft updates through the theme detail endpoint.

Rules:

- Request body must be valid JSON.
- Payload `theme_id` must match the existing theme.
- Payload must validate against the theme configuration schema.
- Updating a draft also updates the theme name and description from the payload.
- A new `ThemeRevision` is created with `draft` status.

The admin detail surface currently focuses on inspection. Editing controls should preserve this validation path when richer authoring UI is added.

## Publishing

Publishing a revision:

1. Finds the requested revision for the theme.
2. Archives other published revisions for that theme.
3. Marks the requested revision as `published`.
4. Sets it as `theme.current_revision`.

Only publish revisions that have passed schema validation and accessibility review.

## Rollback

Rollback uses the same backend path as publishing a previous revision. Rolling back:

- selects a previous revision;
- archives other published revisions;
- marks the selected revision as `published`;
- sets it as current.

Rollback does not edit a published revision. It changes which existing revision is active.

## Troubleshooting

If the theme list does not load:

1. Confirm the tenant query parameter is available to the API client.
2. Confirm the tenant exists.
3. Confirm the user can access the Themes module.
4. Check the admin API response shape includes a `themes` array.

If a theme detail does not load:

1. Confirm the route contains a `themeId`.
2. Confirm the theme exists for the tenant.
3. Confirm the detail response includes a `theme` object.
4. Confirm the current revision includes a payload for token inspection.

If contrast checks are missing:

1. Confirm colors use valid 6-digit hex values.
2. Confirm color scales include both `main` and `contrast`.
3. Confirm modes include both `text` and `background` overrides.

## Validation

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Theme builder behavior changes should also run:

```powershell
python tools/validate_backend.py
cd frontend-admin
npm run validate
```

Theme schema changes should run:

```powershell
python contracts/validate_contracts.py
```
