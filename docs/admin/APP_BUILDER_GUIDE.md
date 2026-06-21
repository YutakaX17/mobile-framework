# App Builder Guide

This guide describes the current app builder baseline for administrators and builders. It focuses on the implemented app library, screen designer inspection panels, validation findings, mobile preview, and publish behavior.

## Access

The Apps module is available to users with `apps:manage` or `platform-admin`.

Routes:

- `/apps`: app library.
- `/apps/:appId`: app designer and current revision inspection.

If the route shows an unauthorized state, confirm the user has the `builder` role or another role that grants `apps:manage`.

## App Library

The app library lists tenant-scoped apps returned by the admin API.

Use the library to review:

- app identifier;
- app name and description;
- current revision status;
- current revision version;
- current revision screen count;
- current revision permission count;
- published app count;
- total screen count;
- total navigation item count.

The Refresh action reloads the app list. Loading, unavailable, and empty states are explicit so administrators can distinguish "no apps exist" from "apps could not load."

## App Designer

The app designer shows the current revision payload for a selected app.

Current designer panels:

- navigation;
- component registry;
- screen canvas;
- app properties;
- permission bindings;
- component properties;
- app validation;
- actions;
- mobile preview.

If no payload is available, the designer shows a no-payload state instead of rendering partial app data.

## Navigation

Navigation items come from the app payload `navigation` array. Each item links a navigation label to a screen identifier.

The navigation panel shows:

- label;
- screen id;
- group, defaulting to `primary`;
- presentation, defaulting to `drawer`;
- order, defaulting to `0`;
- default marker when `is_default` is set.

Navigation can optionally include an icon and permission. Permission references are checked against declared app permissions in the validation panel.

## Component Registry

The component registry lists supported component types in display order:

- Text: display static or bound copy.
- Button: trigger a runtime action.
- Form: render a published form.
- List: render repeated records.
- Card: group related content.
- Image: render an image asset or URL.
- Spacer: control vertical rhythm.
- Custom: module-provided component.

Each registry item also shows how many matching components are present on the current canvas. Keep component type names stable because the admin designer, contracts, and mobile renderer depend on the same schema values.

## Screen Canvas

App payloads are schema-backed configuration packages. Required top-level fields include `schema_version`, `app_id`, `name`, `version`, `navigation`, and `screens`.

Each screen card summarizes:

- screen id;
- name;
- screen type;
- order;
- route;
- layout type;
- display title;
- display icon;
- offline cache strategy;
- sync required state;
- top-level components;
- total component count;
- action count.

Screen types are `dashboard`, `form`, `detail`, `list`, `settings`, and `custom`. Form screens must include at least one component with component type `form`.

The current baseline is an inspection and publish surface. Future editing controls should preserve schema validation and app validation findings before revisions are published.

## Properties

The app properties panel summarizes:

- app id;
- version;
- theme id;
- declared permission count.

Component property summaries include:

- screen name and id;
- component id;
- component type;
- binding;
- child count;
- custom properties.

Component bindings resolve in this order: `form_id`, `data_path`, `action_id`, then `unbound` when none are set.

## Permission Bindings

Permission binding summaries are collected from navigation items, screens, actions, and components.

Each binding shows:

- binding type;
- screen id;
- target id;
- permission code;
- permission label.

Permission labels come from the payload `permissions` array. If a permission is referenced but not declared, the binding remains visible and the validation panel reports a warning.

## App Validation

The validation panel checks references that are important before publishing.

Current validation findings include:

- duplicate screen ids;
- navigation items pointing to missing screens;
- permission references that are not declared;
- component action bindings pointing to missing screen actions;
- action component bindings pointing to missing components;
- navigate action targets that do not match a screen id.

Findings can be errors or warnings. The Publish revision action is disabled when any validation finding has `error` severity.

Schema validation also runs in the backend when app revisions are saved. The app schema, screen schema, component schema, and action schema remain the source of truth for allowed payload structure.

## Actions

The actions panel summarizes screen actions from each screen payload.

Each action summary shows:

- screen id;
- action label;
- action type;
- target;
- binding source and event;
- payload path;
- result path;
- confirmation title;
- success behavior;
- error behavior.

Supported action types are `navigate`, `submit_form`, `open_url`, `start_workflow`, `sync_now`, and `logout`. `navigate`, `submit_form`, and `open_url` actions require a target in the action contract.

## Mobile Preview

The mobile preview renders a compact approximation of each screen.

Each preview screen shows:

- navigation label;
- route;
- title;
- subtitle;
- component tree;
- action labels.

Component previews show the component label, component type, binding, and nested children. The preview is useful for structure review, but the schema and mobile runtime renderer remain the source of truth for published package behavior.

## Publishing

The app designer can publish the current revision when:

- an app is loaded;
- a current revision exists;
- the current revision is not already `published`;
- app validation has no errors.

Publishing uses a backend endpoint for the selected revision. The backend:

1. Finds the requested revision for the app.
2. Archives other published revisions for that app.
3. Marks the requested revision as `published`.
4. Sets it as `app.current_revision`.

Only publish revisions that have passed schema validation, reference validation, permission review, and mobile preview review.

## Troubleshooting

If the app list does not load:

1. Confirm the tenant query parameter is available to the API client.
2. Confirm the tenant exists.
3. Confirm the user can access the Apps module.
4. Check the admin API response shape includes an `apps` array.

If an app designer does not load:

1. Confirm the route contains an `appId`.
2. Confirm the app exists for the tenant.
3. Confirm the detail response includes an `app` object.
4. Confirm the current revision includes a payload with `screens` and `navigation` arrays.

If publishing is disabled:

1. Confirm the app has a current revision.
2. Confirm the current revision is not already published.
3. Review app validation findings for errors.
4. Confirm navigation, action, component, and permission references are valid.

If mobile preview content is incomplete:

1. Confirm screens have components.
2. Confirm navigation items reference existing screens.
3. Confirm component bindings use supported `form_id`, `data_path`, or `action_id` values.
4. Confirm nested component trees validate against the component schema.

## Validation

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

App builder behavior changes should also run:

```powershell
python tools/validate_backend.py
cd frontend-admin
npm run validate
```

App, screen, component, or action schema changes should run:

```powershell
python contracts/validate_contracts.py
```
