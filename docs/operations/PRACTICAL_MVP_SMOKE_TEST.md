# Practical MVP Smoke Test

This guide defines the practical Field Ops smoke path for the end-to-end MVP.

The CI-backed smoke gate is automated through a Django integration test. It does not start long-running servers; it uses the real Django URL routing, seed command, package publication APIs, mobile package delivery APIs, sync APIs, and database models in one transaction-backed test database.

## Automated Smoke Gate

Run the focused smoke path from the repository root:

```powershell
python tools/validate_practical_mvp_smoke.py
```

This executes:

```powershell
python backend/manage.py test tests.test_integration.PracticalMvpBuilderIntegrationTests.test_practical_mvp_smoke_path_from_admin_publish_to_mobile_sync --settings=config.settings.test
```

The test verifies:

- `seed_demo_mvp` creates the demo tenant, admin user, Field Ops module, published builder revisions, release channels, active package, and seed audit events.
- The demo admin can log in through the backend auth API.
- The Field Ops module status endpoint reports the plugin as enabled.
- Theme, form, and app drafts can be updated and published.
- A new dev deployment package can be compiled and activated.
- The mobile active manifest endpoint returns the activated package.
- The mobile package download endpoint returns the package payload and matching hash.
- A runtime-style device can register with sync.
- A sample offline-style form submission can be sent through the outbox API.
- Sync status exposes the processed batch and receipt.
- The backend stores the form submission, outbox batch, sync result, and sync audit event.

The same path is also covered by:

```powershell
python tools/validate_backend.py
```

## Manual Local Smoke Path

Use the manual path when validating the browser and runtime surfaces on a workstation.

Install backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Prepare the local database:

```powershell
python backend/manage.py migrate
python backend/manage.py seed_demo_mvp
```

Start the backend:

```powershell
python backend/manage.py runserver 127.0.0.1:8000
```

In another terminal, start the admin frontend:

```powershell
cd frontend-admin
npm ci
npm run dev
```

Open the admin frontend and sign in with the local demo account:

- Username: `demo-admin`
- Password: `demo-admin-password`

Then verify:

1. The dashboard loads for tenant `demo`.
2. The setup page shows the Field Ops plugin as enabled.
3. The package release page can publish and activate a `dev` package.
4. The mobile connection details show the active manifest URL and package download URL.

Fetch the mobile package from a terminal:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/mobile/packages/manifest/?tenant=demo&app_id=field_ops_app&channel=dev"
Invoke-RestMethod "http://127.0.0.1:8000/api/mobile/packages/pkg_demo_field_ops_001/download/?tenant=demo"
```

Register a runtime device and submit a sample outbox batch:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/mobile/sync/devices/" -Method Post -ContentType "application/json" -Headers @{"X-Tenant-Slug"="demo"} -Body '{"device_id":"field-tablet-local-1","platform":"android","runtime_version":"0.1.0","app_version":"0.1.0"}'
Invoke-RestMethod "http://127.0.0.1:8000/api/mobile/sync/outbox/" -Method Post -ContentType "application/json" -Headers @{"X-Tenant-Slug"="demo"} -Body '{"batch_id":"manual-smoke-batch-001","device_id":"field-tablet-local-1","platform":"android","runtime_version":"0.1.0","app_version":"0.1.0","submissions":[{"client_submission_id":"manual-smoke-submission-001","form_id":"patient_intake","answers":{"patient_name":"Amina Nkosi","age":34,"triage_priority":"routine"}}]}'
Invoke-RestMethod "http://127.0.0.1:8000/api/mobile/sync/status/?device_id=field-tablet-local-1" -Headers @{"X-Tenant-Slug"="demo"}
```

Run the admin and mobile validation suites before treating the smoke pass as complete:

```powershell
python tools/validate_frontend_admin.py
python tools/validate_mobile.py
python tools/validate_mobile_tests.py
```

Full Gradle runtime tests run in CI. A local Gradle installation or wrapper is required to run them on a workstation.
