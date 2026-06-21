# Backup And Restore Guide

This guide describes the current backup and restore baseline for the mobile framework. It focuses on PostgreSQL data protection, local Docker Compose recovery practice, restore verification, retention expectations, and storage areas that still need production-specific runbooks.

## Current Baseline

The current local infrastructure baseline includes:

- PostgreSQL 16 in `infra/compose/docker-compose.yml`;
- database name `mobile_framework`;
- database user `mobile_framework`;
- local Compose volume `postgres_data`;
- Redis for runtime cache/queue dependencies.

Redis is not a system of record in the current baseline. PostgreSQL is the primary data store that must be backed up and restored.

Object storage, media uploads, and external file storage are not implemented in the current repository baseline. When those are added, they must receive separate backup and restore procedures.

## Backup Scope

Back up PostgreSQL data before:

- applying migrations in a shared environment;
- promoting deployment packages to staging or production;
- rotating database credentials;
- upgrading PostgreSQL versions;
- changing tenant, identity, configuration, package, workflow, or audit models;
- running destructive maintenance scripts.

Backups should include enough metadata to identify:

- environment;
- database name;
- backup timestamp;
- application commit or release version;
- operator;
- retention class;
- checksum.

## Local Compose Backup

Start the local database before taking a local backup:

```powershell
docker compose -f infra/compose/docker-compose.yml up -d postgres
```

Create a plain SQL backup from the local Compose database:

```powershell
docker compose -f infra/compose/docker-compose.yml exec postgres pg_dump --username mobile_framework --dbname mobile_framework --no-owner --no-privileges > build/backups/mobile_framework.sql
```

Create the output directory first when needed:

```powershell
New-Item -ItemType Directory -Force build/backups
```

Record a checksum for the backup file:

```powershell
Get-FileHash build/backups/mobile_framework.sql -Algorithm SHA256
```

Do not commit backup files. Backup artifacts belong in controlled storage, not in the repository.

## Local Compose Restore

Stop services that may write to the database before restoring:

```powershell
docker compose -f infra/compose/docker-compose.yml stop backend frontend-admin
```

For a clean local restore, recreate the PostgreSQL volume:

```powershell
docker compose -f infra/compose/docker-compose.yml down
docker volume rm mobile-framework_postgres_data
docker compose -f infra/compose/docker-compose.yml up -d postgres
```

Restore the SQL backup:

```powershell
Get-Content build/backups/mobile_framework.sql | docker compose -f infra/compose/docker-compose.yml exec -T postgres psql --username mobile_framework --dbname mobile_framework
```

Restart dependent services after the restore:

```powershell
docker compose -f infra/compose/docker-compose.yml up -d backend frontend-admin
```

The local backend and frontend-admin Compose services are placeholders in the current baseline. Use the Django validation commands below to verify repository-level health after local restore drills.

## Production-Like Backup

Production-like environments should use managed database snapshots or a controlled `pg_dump` process with encrypted artifact storage.

Minimum expectations:

- encrypted backup storage;
- restricted restore permissions;
- daily automated backups for active environments;
- backup checksums;
- retention policy by environment;
- restore drill cadence;
- documented recovery time objective;
- documented recovery point objective.

Recommended retention baseline:

- development and test: short retention, such as 7 days;
- staging: medium retention, such as 14 to 30 days;
- production: daily backups for at least 30 days, plus longer monthly snapshots when required by the deployment context.

Adjust retention to the actual compliance requirements of the environment being deployed.

## Restore Verification

After restoring PostgreSQL data, verify:

1. Django migrations are consistent.
2. Required tenants are present.
3. Identity and role records are present.
4. Configuration revisions load.
5. Deployment packages and current active package pointers are intact.
6. Audit events are readable.
7. Workflow tasks reference valid workflow states.
8. Local validators pass.

Run repository validation:

```powershell
python tools/validate_foundation.py
python tools/validate_backend.py
python contracts/validate_contracts.py
```

For production-like restores, also perform an application smoke test against the restored environment before reopening write traffic.

## Migration Safety

Before applying migrations to shared environments:

1. Confirm the target commit or release version.
2. Take a fresh database backup.
3. Record the backup checksum.
4. Confirm restore credentials are available.
5. Confirm rollback expectations for code and data.
6. Apply migrations.
7. Run smoke tests.
8. Keep the backup until the release is accepted.

Avoid applying destructive migrations without a tested restore path.

## Object Storage And Media

Object storage and uploaded media are not implemented in the current baseline.

When those capabilities are added, the backup plan must cover:

- object bucket names;
- object versioning settings;
- lifecycle rules;
- encryption;
- restore procedure;
- object checksum validation;
- relationship between database records and object keys.

Database backups alone will not be sufficient once package assets, uploaded documents, images, or generated files are stored outside PostgreSQL.

## Incident Restore Checklist

During an incident restore:

1. Freeze writes if data corruption is suspected.
2. Identify the restore target time.
3. Select the newest backup before the target time.
4. Verify backup checksum.
5. Restore into an isolated environment first when possible.
6. Run restore verification.
7. Confirm application version compatibility.
8. Promote the restored environment or restore the target environment.
9. Record the incident, operator, backup id, restore time, and validation results.
10. Review whether retention or monitoring needs adjustment.

## Troubleshooting

If `pg_dump` cannot connect:

1. Confirm the Compose PostgreSQL service is running.
2. Confirm `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` match the Compose file.
3. Confirm port `5432` is not blocked or mapped to another local service.

If restoring into Compose fails:

1. Confirm the destination database exists.
2. Confirm the SQL file is not empty.
3. Confirm the `docker compose exec -T` command is used when piping input.
4. Recreate the `postgres_data` volume for a clean restore if conflicts are expected.

If validation fails after restore:

1. Confirm the backup came from a compatible application version.
2. Confirm migrations have been applied for the current code.
3. Confirm tenant-scoped records reference matching tenants.
4. Check model validation errors for stale or incompatible JSON payloads.

## Validation Commands

Documentation-only changes to this guide should run:

```powershell
python tools/validate_docs_site.py
python tools/validate_foundation.py
python tools/validate_python.py
```

Backup or restore automation changes should also run:

```powershell
python tools/validate_backend.py
python contracts/validate_contracts.py
```
