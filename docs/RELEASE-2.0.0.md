# Paperless-ngx module 2.0.0

Upgrade to **Paperless 3.5.0**, the current verified stable upstream release, from
the required **Paperless 2.20.15** checkpoint in module **1.4.0**.

This is a major module release because upstream changes search, task history,
consumer/OCR configuration and custom-script conventions. Document originals,
archives, metadata, credentials and original signing keys are preserved; the
behavior changes below are documented explicitly.

## Requirements and enforced path

- **NS8 core 3.0.0 or later**.
- Existing installations follow **1.3.1 → 1.3.2 → 1.4.0 → 2.0.0**.
- The image carries `org.nethserver.min-from=1.4.0` for catalog clients.
- First-time v3 upgrades require a healthy **2.20.15** checkpoint and a matching
  database migration fingerprint. A previous-version string alone is insufficient.
- The guard runs before update restart and again before the container entrypoint
  can run migrations. Forced jumps and direct service startup cannot skip it.
- On x86_64, all CPUs must support the **x86-64-v2** instruction baseline required
  by upstream NumPy. Unsupported hardware is blocked rather than silently losing
  classifier functionality. ARM hosts are not subject to the x86 instruction test.

## Runtime versions

| Component | Version |
| --- | --- |
| Paperless-ngx | **3.5.0** |
| PostgreSQL | **15.20-bookworm** |
| Redis | **7.2.16-bookworm** |
| Gotenberg | **8.40.0** |
| Apache Tika | **3.3.3.0-full** |

The database remains on PostgreSQL major version 15. Existing named volumes,
database credentials and signing keys are retained.

## Safe preparation and recovery

- A protected pre-migration database dump and configuration copies are retained
  under module state `upgrades/2.0.0/`.
- Copies and checkpoint writes are atomic. Backup failure cannot authorize the
  target application to migrate its database.
- Preparation journals recover interrupted configuration conversion before a
  retry. A freeze journal recovers an application paused by interrupted preparation.
- The target configuration fingerprint is checked before startup; unexpected
  changes after preparation require review.
- Upgrade checkpoints, original timestamp archives and recovery files are included
  explicitly in NS8/Restic backups and verified by clean-instance restore tests.
- These local recovery aids supplement a verified full backup of database, media
  and state. They do not replace that backup or make an image-only downgrade safe.

## Configuration compatibility

- Set the PostgreSQL engine explicitly, as required by v3.
- Translate the old OCR modes and archive-generation preferences to the v3
  settings. Preserve the v2 default of always generating archives.
- Explicitly retain duplicate rejection. In v2, a false delete-duplicates flag
  still rejected duplicate documents; v3 false would allow them. Operators can
  opt into the new duplicate behavior after migration.
- Translate consumer polling and stability delays. Retired retry/barcode-scanner
  variables are removed, and reviewed glob patterns are converted to regular
  expressions. Upstream v3 ignore defaults remain additive.
- Consolidate deprecated PostgreSQL SSL, timeout and pool options into
  `PAPERLESS_DB_OPTIONS`, preserving explicitly supplied new options.
- Default Allauth's trusted proxy count to the module's single Traefik HTTP hop;
  retain an explicitly configured count for installations with additional proxies.
- Preserve unrelated custom settings and the original credentials/signing key.

## Conditions requiring action before migration

- **Encrypted documents:** decrypt them on 2.20.15 first. The guard blocks legacy
  encrypted storage and a remaining legacy passphrase setting.
- **Mail rules:** review `maximum_age` values above 32767. The module blocks
  silent clamping of these values.
- **Custom consume scripts:** replace positional arguments with the documented
  `DOCUMENT_*` environment variables, which are also available in v2.
- **Custom ignore patterns:** review v3's regex/additive-default behavior.
- **Saved searches:** review ambiguous unqualified searches when notes or custom
  fields exist; their implicit search scope changes in v3.
- **Shared saved-view visibility:** ownerless views with global dashboard/sidebar
  flags require review. Upstream moves visibility into per-user preferences;
  owned-view preferences migrate automatically, while shared/global choices may
  need explicit per-user reconfiguration.
- **OIDC:** specify the intended token authentication method or review the provider
  configuration before proceeding.
- **OCR user arguments:** remove reserved input/output arguments (`sidecar`,
  `output_file`, `input_file_or_options`) before 3.5. The guard checks both
  environment and database configuration instead of silently ignoring them.

Review acknowledgements are bound to a fingerprint of the actual configuration
and relevant saved queries. Changes invalidate the previous acknowledgement.
See [the administrator review procedure](V3-ADMIN-REVIEW.md).

## Upstream changes to expect

- **Search:** Whoosh is replaced by Tantivy. The first startup rebuilds the index.
  Allow enough time and disk space for a large collection.
- **Saved-view field names:** upstream rewrites explicit `note:` queries to
  `notes.note:` and `custom_field:` to `custom_fields.value:`. Tests verify that
  the migrated note search still finds the original document.
- **Task history:** upstream recreates its task tables. The old task history no
  longer appears in the v3 task list. Before migration, the module exports the
  original task and Celery-result rows to protected JSONL files alongside the
  database backup so the historical records remain recoverable.
- **Barcode scanning:** zxing-cpp replaces pyzbar; the obsolete backend setting
  is removed.
- **API:** v3 supports API versions 9 and 10. Older versioned clients must be
  updated. Unversioned clients use version 10; saved-view visibility moved to
  per-user settings, with the version-9 compatibility interface retained.
- **Paperless 3.5:** bulk operations use asynchronous hand-off, manual workflow
  triggers are available, and notes support Markdown. Existing plain-text notes
  retain their plain format; tag parent relationships are preserved while the
  internal tree implementation changes.
- **Document-created dates:** the earlier 1.4.0 checkpoint already performs the
  timestamp-to-date migration. Its exact original timestamp archive is retained
  through this upgrade and backup/restore.

## Verification and release artifacts

- Debian 13 tests fresh installation; Rocky Linux 9 tests the real upgrade path
  in parallel.
- Negative checks reject skipped checkpoints, direct startup and encrypted
  documents before migrations.
- Fixtures cover PDF, DOCX and email ingestion, original/archive bytes, calendar
  dates, tag hierarchies, correspondents, document types, custom fields, plain-note
  format and saved views. The original API token is checked for preservation.
- Authentication checks exercise both API tokens and browser-form session login
  through Traefik, including cookies and CSRF tokens.
- Both OS roles perform a full NS8/Restic backup, delete the disposable source
  instance, restore a clean instance and verify data, secrets, configuration,
  Redis and recovery archives.
- The release includes a scoped CycloneDX SBOM, immutable image references and
  checksums. Source/build dependency findings are disclosed separately; the SBOM
  is not a claim that every external image package has been transitively inventoried.

Detailed CI results are recorded in the final GitHub release notes. Existing NS8
frontend source dependency advisories remain a separate remediation/reachability
review; this module release is not described as a clean frontend security audit.

## Production update procedure

1. Verify module **1.4.0** and its Paperless **2.20.15** checkpoint.
2. Read the upstream [v3 migration guide](https://github.com/paperless-ngx/paperless-ngx/blob/v3.5.0/docs/migration-v3.md)
   and resolve applicable review conditions above.
3. Quiesce ingestion, take and verify a full backup, reserve free storage and
   schedule a maintenance window.
4. Update to **2.0.0**, allowing time for database migrations and search rebuild.
5. Verify browser login, consumption, conversions, downloads, metadata, saved
   views, search, mail integration and a new backup before resuming normal work.
6. Retain matching pre-upgrade database/media/state backups. Rollback requires
   restoring them together, not selecting the old image against the migrated DB.
