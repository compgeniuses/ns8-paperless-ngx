# Paperless-ngx module 1.3.2

Stable compatibility and supporting-service update for existing NethServer 8
Paperless-ngx installations. This is the first checkpoint in the staged upgrade
path from module 1.3.1 toward the current Paperless application release.

**Paperless remains at 2.11.4.** This release preserves the application baseline
while updating its supporting services and strengthening configuration,
credentials, backup, restore and upgrade handling. The known upstream security
limitations of Paperless 2.11.4 remain; see the security section below.

## Requirements and upgrade path

- **Minimum NS8 core: 3.0.0.** Update and validate older core installations before
  offering this module release. NethForge retains module 1.3.1 for older cores.
- **Validated starting release: module 1.3.1**, including the intermediate
  1.3.2-testing.1 compatibility build and the final dependency refresh.
- **Planned stable checkpoints: 1.3.1 → 1.3.2 → 1.4.x → 2.0.x.**
- Module 1.4.x is planned to provide Paperless **2.20.15**, the upstream
  prerequisite for moving to Paperless v3. Module 2.0.x will carry the v3
  application transition. Those later releases are separate work.
- This release does not implement the future 1.4.x/2.0.x minimum-from labels or
  runtime guards. Those must be delivered and tested with the corresponding
  future release; pins alone do not protect direct CLI updates.

## Application and supporting services

| Component | Module 1.3.1 | Module 1.3.2 |
| --- | --- | --- |
| Paperless-ngx | 2.11.4 | **2.11.4** |
| PostgreSQL | 15.5-bookworm | **15.20-bookworm** |
| Redis | 7.2.3-bookworm | **7.2.16-bookworm** |
| Gotenberg | 8.9.1 | **8.40.0** |
| Apache Tika | 3.0.0.0-BETA2-full | **3.3.3.0-full** |

- PostgreSQL remains on major version 15, avoiding a database major-version
  migration at this checkpoint.
- Redis remains on the 7.2 line; the update does not flush its stored data.
- The full Apache Tika variant is retained to preserve its parser dependencies.
- Existing named volumes, database account details, signing keys, module identity
  and application settings are preserved.

## Configuration and credentials

- Partial configuration requests preserve omitted values and custom settings.
- Leaving the administrator password blank keeps the existing password. On first
  configuration, the module generates a random password if none is supplied.
- Read-only configuration responses no longer disclose the stored administrator
  password; the settings page supports leaving the existing password unchanged.
- Secret environment files are protected with restrictive permissions.
- Legacy 1.x environment settings and the original signing key are recovered into
  protected state files without replacing existing file overrides or silently
  rotating credentials.
- Database and signing-key discovery use original stored values instead of
  inventing replacement credentials at service startup.

## Service startup, mail and update reliability

- Pod members have explicit startup ordering. Module updates restart every
  required child service so the requested image changes take effect.
- Restore handling preserves custom database account names and correctly handles
  missing legacy keys and saved route booleans.
- SMTP discovery uses Paperless's actual SMTP settings and selects STARTTLS or
  implicit TLS as appropriate. Certificate verification remains enabled.
- Mail changes refresh the application service without unnecessarily restarting
  the entire supporting stack.
- Concurrent SMTP discovery processes use separate temporary files before atomic
  replacement, avoiding collisions during simultaneous service startup.

## Backup and restore

- Database dumps are replaced atomically only after a successful dump. A failed
  dump does not overwrite the last usable backup file.
- Diagnostics are kept out of action output intended for machine parsing.
- Automated checks restore a populated PostgreSQL dump into a clean database.
- Full NS8/Restic checks back up a populated disposable instance, delete that
  source instance, restore a clean module and compare the resulting data.
- Restored checks cover original and archived documents, metadata, extracted
  text, dates, search, authentication, configuration, database credentials,
  signing keys and persisted Redis key/list data.
- The consistency test pauses the disposable application and Redis containers
  while the snapshot is captured. This release does not automatically pause
  production document ingestion or change existing backup schedules. Quiesce
  ingestion when taking the pre-upgrade rollback backup.

## NS8 integration, interface and translations

- Replace the old DigitalOcean test workflow with the standard NS8 QEMU workflow.
- Publish a minimum-core label and refresh listing categories, descriptions,
  documentation, source and issue links.
- Use NS8 settings components and isolate task progress and completion events.
- Pin the build-only Node runtime to **22.22.0-bookworm** and use frozen UI
  dependency installation for reproducible builds.
- Complete all **54 English and Italian translation keys**, including the
  password guidance, configuration progress and domain-conflict messages.

## Validation

The published **1.3.2-testing.2** image passed QEMU validation on **Debian 13**
and **Rocky Linux 9**:

- Upgrade scenarios: **12 tests passed**, with no failures.
- Fresh-install scenarios: **11 tests passed**, with only the upgrade-specific
  test skipped.
- Real PDF, DOCX and email fixtures were ingested before the update; new Office
  and email files were converted after the dependency update.
- Original/archive hashes, document text and dates, login, search, original
  secrets and Redis markers were verified across updates and clean restores.
- Nine local regression tests and the module contract, image-publication and API
  documentation workflows passed.

Evidence: [published testing image QEMU run](https://github.com/compgeniuses/ns8-paperless-ngx/actions/runs/43925248274),
[Debian upgrade and Rocky installation](https://github.com/compgeniuses/ns8-paperless-ngx/actions/runs/43922966653),
and [Rocky upgrade and Debian installation](https://github.com/compgeniuses/ns8-paperless-ngx/actions/runs/43919914773).

Older 1.x layouts received source review and regression checks for legacy state
migration. A populated end-to-end upgrade of every historical 1.x release has
not been demonstrated. Custom scripts, extensions, indexes, collations, mail
workflows and production-specific document sets need instance-specific review.

## Before updating a production instance

1. Confirm NS8 core is at least 3.0.0 and that sufficient free storage is
   available.
2. Quiesce document ingestion, take a verified backup of the database, media and
   module state, and confirm the restore procedure.
3. Review PostgreSQL's cumulative 15.x migration notes, including
   [15.20](https://www.postgresql.org/docs/release/15.20/). Some index fixes require
   a targeted `REINDEX`; a container restart does not repair an affected index.
   No database-wide `REINDEX` runs automatically.
4. Schedule a maintenance window: services restart and the application is
   temporarily unavailable during the update.
5. After updating, check login, document consumption, conversion, downloads,
   search, mail settings and a new backup.
6. If rollback is necessary, restore the matching database, media and state
   backup together. Changing only the image tag is not a reliable rollback.

The stock fresh-install CI schema recorded **264 btree indexes**, with no
GIN/GiST indexes or unconstrained bpchar operator class. This does not establish
that a customized production database needs no index maintenance.

## Known security limitations

Paperless 2.11.4 is deliberately retained for this migration checkpoint. Updating
the supporting containers does **not** incorporate later Paperless security
fixes. Published advisories affecting this application baseline include:

- [Authenticated users can download other users' documents through bulk download](https://github.com/paperless-ngx/paperless-ngx/security/advisories/GHSA-g6fw-vp8x-gr4j),
  fixed upstream in 2.14.0. The upstream workaround disables other user accounts.
- [Document editors can alter document permissions](https://github.com/paperless-ngx/paperless-ngx/security/advisories/GHSA-w47q-3m69-84v8),
  fixed upstream in 2.20.6.
- [Share-link creation does not enforce document-level authorization](https://github.com/paperless-ngx/paperless-ngx/security/advisories/GHSA-386h-chg4-cfw9),
  fixed upstream in 2.20.9.

The frontend dependency audit also reports existing advisories. Audit findings
include browser dependencies and build-tool dependencies; dependency presence
alone does not prove that every reported issue is exploitable in the deployed
interface. This release is not represented as free of known vulnerabilities.
Review the security findings and continue to the patched application checkpoint
when it becomes available; 1.3.2 is a migration checkpoint, not the final endpoint.

## Software inventory

The release includes a **CycloneDX JSON SBOM** (`.cdx.json`) and checksum file.
Its scope is the module source dependency inventory and immutable references to
the published module image and supporting runtime images. Runtime image
references are not a transitive inventory of every package inside those images.
The SBOM is an inventory, not a declaration that the listed software is
vulnerability-free.

## Changes and NethForge tracking

- [PR #35: compatibility, state preservation and QEMU baseline](https://github.com/compgeniuses/ns8-paperless-ngx/pull/35).
- [PR #36: supporting-service refresh and full restore validation](https://github.com/compgeniuses/ns8-paperless-ngx/pull/36).
- [NethForge pins PR #52](https://github.com/NethServer/ns8-nethforge/pull/52)
  preserves the planned checkpoints. Review may proceed before future releases;
  unpublished image checks remain open until the corresponding tags exist.
