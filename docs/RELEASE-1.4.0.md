# Paperless-ngx module 1.4.0

Paperless **2.20.15** is the application checkpoint required before the v3
transition. Upgrade existing installations through stable module **1.3.2** first.
NS8 core **3.0.0** or later is required.

## Application and services

- Paperless moves from **2.11.4** to **2.20.15**.
- PostgreSQL remains **15.20-bookworm**, Redis **7.2.16-bookworm**, Gotenberg
  **8.40.0**, and Apache Tika **3.3.3.0-full**.
- There is no PostgreSQL major-version migration at this checkpoint.
- Existing volumes, original signing key, database credentials, configuration,
  document originals and archives are preserved.

## Enforced upgrade checkpoint

- The image advertises `org.nethserver.min-from=1.3.2` for catalog clients.
- The update hook validates the previous stable module version before restart.
- The server startup repeats the guard before Paperless's entrypoint can run
  migrations. NS8 continues after a failed update hook, so an isolated failing
  hook would not provide this protection.
- A forced 1.3.1 → 1.4.0 jump is rejected, including a direct service restart.
  The application database is not migrated by the rejected jump.
- After a successful migration, the module checks the running Paperless version
  and HTTP health before recording its 1.4 checkpoint and database migration
  fingerprint. An unrelated or mismatched database cannot reuse that checkpoint.
- Fresh installations are supported separately from upgrades. A fresh-install
  marker does not authorize importing a populated legacy database that skipped
  the required checkpoint.

## Backup and migration handling

- Before migration, the module briefly pauses the application while taking a
  database dump and copying the original configuration and credentials into the
  protected state directory `upgrades/1.4.0/`.
- A failed dump unpauses the existing application and does not authorize the new
  entrypoint to migrate its database.
- The first pre-migration dump is retained across retries. These local files are
  additional recovery aids; take a verified full NS8 backup, including media and
  state, before upgrading.
- Paperless 2.17 changes document `created` from a timestamp to a calendar date.
  The upstream migration uses the configured timezone. Exact original timestamps
  are preserved separately in `original-created-timestamps.jsonl`, indexed by
  document ID; the application's API now returns a date.

## Upstream behavior to review

- The application webserver changes to Granian. Routing and conversion tests use
  the actual NS8 Traefik route and module port. Review any custom webserver or
  reverse-proxy options against the upstream configuration guide.
- API consumers must accommodate the document `created` date representation.
- The upstream database migrations update scheduled workflow offsets and other
  schema details. Review custom integrations and scheduled workflows after the
  upgrade.
- Paperless 2.20.15 incorporates the upstream access-control fixes identified in
  the 1.3.2 compatibility-release notes. Existing NS8 UI dependency findings
  remain a separately documented remediation task.

## Validation scope

- Fresh installation runs on **Debian 13**; upgrades run on **Rocky Linux 9** in
  parallel, with fixed roles rather than rotating scenarios.
- Upgrade checks begin with populated module 1.3.1, prove that skipping 1.3.2 is
  rejected, recover the disposable instance to 1.3.2, then perform the supported
  update to this application checkpoint.
- Real PDF, DOCX and email files are consumed before and after migration.
- Preservation checks cover original/archive hashes, text, calendar dates, tags,
  correspondents, document types, custom fields, notes, saved views,
  authentication, search, original credentials and Redis persistence.
- Both roles perform a full NS8/Restic backup, delete the disposable source
  instance, restore a clean module and compare the restored data and configuration.
- Unit checks cover rejected sources, missing preparation, backup failure,
  unpausing the original application, retry preservation and checkpoint/schema
  mismatch.

Detailed CI results and the CycloneDX SBOM are attached to the GitHub release
after these checks complete. The SBOM includes source dependency inventory and
immutable module/runtime image references, with its scope stated explicitly.

## Production update procedure

1. Update to stable **1.3.2** and verify the existing installation first.
2. Quiesce ingestion and take a verified full backup of the database, media and
   module state. Reserve a maintenance window and sufficient free storage.
3. Update to **1.4.0**. Do not bypass the checkpoint or delete safety-state files.
4. Verify login, consumption, Office/email conversion, downloads, notes, custom
   fields, saved views, search, mail integration and a new backup.
5. Retain the pre-upgrade backup until the application and integrations are
   verified. Rollback requires restoring matching database, media and state;
   changing only an image tag is not a reliable rollback.

The next planned application transition is module **2.0.0**, using upstream
Paperless v3 from this exact **2.20.15** checkpoint.
