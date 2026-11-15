# Backup & recovery

## Database backups
- **Render Postgres** takes automatic daily backups and supports point-in-time restore on paid plans -
  confirm the plan and retention window in the Render dashboard; this is a platform feature, not
  something this codebase implements.
- **Manual backup** (from any environment with `pg_dump`):
  ```
  pg_dump "$DATABASE_URL" -Fc -f backup-$(date +%Y%m%d-%H%M).dump
  ```
- **Restore**:
  ```
  pg_restore --clean --if-exists -d "$DATABASE_URL" backup-YYYYMMDD-HHMM.dump
  ```
  Test restores against a staging database before ever running this against production.

## Document storage backups
- **Local storage backend** (`STORAGE_BACKEND=local`): back up the `uploads_dev` (or configured
  `UPLOAD_DIR`) directory alongside the database. This backend is meant for development only.
- **S3 backend** (`STORAGE_BACKEND=s3`, recommended for production): rely on the bucket provider's own
  versioning/replication (e.g. S3 versioning, cross-region replication) rather than a custom backup job.

## What is NOT backed up automatically by this codebase
- Rate-limiter state (in-memory, deliberately ephemeral).
- `.env` files / secrets - keep these in a password manager or your platform's secret store, not in a
  backup archive.

## Recovery drill checklist
1. Restore the latest database dump into a fresh staging database.
2. Point a staging backend at it and run `alembic upgrade head` to confirm the schema matches.
3. Confirm `/health/db` returns 200.
4. Spot-check a handful of shipments and tracking numbers against what customers would expect.
