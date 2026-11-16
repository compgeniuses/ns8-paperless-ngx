# Paperless-ngx production upgrade investigation

Baseline: NS8 module `1.3.1`, application `2.11.4`. Checked 2026-11-16.

This is a staged migration, not an unconditional image refresh. No claim of zero
impact can be made until an upgrade of an existing populated instance, backup and
restore have passed. Changing only the image back after database migrations is
not a rollback: restore the matching database and document volumes together.

## Verified sources

- [NethServer module skill](https://github.com/NethServer/agents/tree/main/skills/nethserver-ns8-module)
- [Kickstart QEMU workflow](https://github.com/NethServer/ns8-kickstart/blob/main/.github/workflows/test-module.yml)
- [App listing requirements](https://github.com/NethServer/ns8-apps#quality-score)
- [Paperless changelog](https://github.com/paperless-ngx/paperless-ngx/blob/main/docs/changelog.md)
- [v3 migration guide](https://github.com/paperless-ngx/paperless-ngx/blob/main/docs/migration-v3.md)
- [Current stable v3.4.2](https://github.com/paperless-ngx/paperless-ngx/releases/tag/v3.4.2)

The uploaded investigation is useful context, but its proposed 2.15.3 and 2.17.1
stops are testing candidates, not mandatory upstream release checkpoints. The
upstream v3 guide explicitly requires application **2.20.15** before v3. The
webserver change discussed here concerns Paperless/Granian, not Matomo.

## First compatibility candidate

Published baseline: **1.3.2-testing.1**, from commit `8467cbd`.

The [dependency refresh](DEPENDENCY-UPDATE-1.3.2.md) is published as
**1.3.2-testing.2**, with Paperless still 2.11.4. Stable **1.3.2** promotes this
compatibility checkpoint with completed Italian translations and a release SBOM.
See the [stable notes](RELEASE-1.3.2.md) and
[release review](RELEASE-CHECKLIST-1.3.2.md), including inherited security limits.
The original baseline runtime versions below describe the immutable testing.1 tag.

Keep runtime images unchanged: Paperless 2.11.4, PostgreSQL 15.5-bookworm,
Redis 7.2.3-bookworm, Gotenberg 8.9.1, Tika 3.0.0.0-BETA2-full. The build-only Node
image is pinned to verified 22.22.0-bookworm. Do not combine runtime dependency
upgrades, PostgreSQL major changes, and application migrations in this candidate.

Implemented in this branch:

- Standard QEMU workflow replacing DigitalOcean infrastructure; real HTTP routing
  checks replace kickstart placeholders. Install and 1.3.1-update scenarios ingest
  and download a real PDF, compare text/dates, preserve original secret files,
  and restore the populated dump into an isolated clean database.
- Minimum core label; correct image-cleanup name; real metadata documentation,
  source and issue links, standard categories and translated description.
- Preserve omitted and custom configuration values. Blank admin password means
  retain the existing value; fresh installations generate a random password if
  one is not supplied. Store secret environment files with mode 0600.
- Read-only configuration no longer returns the stored admin password; the UI
  accepts an unchanged/blank password. This is intentional security hardening.
- No guessed database credentials or signing-key regeneration on service startup.
  Older 1.x settings/keys are recovered from their original environment into
  protected files; existing file overrides win and secret copies are removed
  from the legacy environment after migration.
- Explicit pod/child ordering and restart lists; restore tolerates absent legacy
  keys, uses restored database account names and parses route booleans correctly.
- Atomic database dump replacement; diagnostics do not contaminate action stdout.
- Real Paperless SMTP variables with correct STARTTLS/implicit-TLS selection;
  a mail event refreshes only the application. Certificate verification remains
  enabled because Paperless 2.11.4 has no verification toggle.
- Reconciled action schemas and preserved partial route settings; deprecated
  ignored inputs remain accepted for API compatibility.
- NS8 input/toggle/tile components, isolated settings task events and progress
  reporting; existing UI library version aligned with its
  lockfile. Archive URLs use the npm registry without changing locked versions.

Existing named volumes, signing key, database credentials, package name and ports
are retained. No production configuration is rewritten by publishing a branch.

## Local validation

Nine regression tests pass, covering partial configuration, secret non-disclosure,
failed/successful backup replacement, original credentials and signing-key
preservation, legacy upgrade/restore conversion, and SMTP transport selection.
Python/JSON/bash syntax and whitespace checks pass. The frozen UI install and
production build pass with existing lint, browser-data and bundle-size warnings.
GitHub module contracts, image publication and API documentation builds pass.

The published testing.2 image passed QEMU installation and populated 1.3.1 upgrade
on Debian 13 and Rocky 9, including real PDF/DOCX/EML consumption, new conversions,
file/archive/metadata preservation, authentication/search, Redis persistence,
isolated database restore and complete NS8/Restic restore after deletion of the
source CI module. [Published-image results](https://github.com/compgeniuses/ns8-paperless-ngx/actions/runs/43925248274).

The new minimum-core label requires NS8 core 3.0.0 or later; check the actual
production nodes before offering this candidate. Older nodes need an independently
validated core update first.

## Remaining conformity/production validation

The installation, populated 1.3.1 update, repeated configuration, document and
secret preservation, new conversions, populated database restore and complete
NS8/Restic restore checks have passed. The restore consistency test pauses the
disposable CI application/Redis containers; production ingestion is not
quiesced automatically by this release.

The stable compatibility checkpoint retains disclosed limitations:

- Frontend auditing reports existing dependency advisories; a separate
  reachability/remediation review remains necessary. Build-tool findings are not
  automatically deployed-interface vulnerabilities.
- Paperless 2.11.4 has published access-control and other upstream advisories.
  Stable 1.3.2 retains that baseline as an explicitly requested staged-upgrade
  checkpoint; it does not claim a clean security audit. Later patched
  application updates remain necessary.
- Populated end-to-end upgrades from every historical 1.x tag are not covered by
  the current QEMU scenarios; legacy state source review and unit checks have
  narrower scope.
- Add the repository `ns8` topic: the connected GitHub installation returned
  HTTP 403 for repository-topic administration, so this remains a maintainer
  action. Verify forge logo/screenshot/metadata quality when updating NethForge.

## Existing stable release layouts

Source review of every stable tag shows PostgreSQL 15.5-bookworm and Redis
7.2.3-bookworm throughout the 1.x line. Paperless versions were 2.2.1 (module
1.0.0), 2.3.1 (1.1.0), 2.3.2 (1.1.1), 2.4.2 (1.2.1), then 2.11.4 (1.3.0/1.3.1).
Before 1.3, application settings and the signing key lived in the module
environment. Upgrade discovery now migrates those originals without replacing
file values, and restore stages legacy snapshot values before inherited Restic
restore. Repeat migration is covered by regression tests. Full populated upgrade
coverage for those older release images remains follow-up validation; the
1.3.2 evidence must not be represented as covering every historical tag.

## Proposed release count (not release approval)

The minimum candidate sequence is three module releases; publish additional
bridges only if migration tests demonstrate they are needed. Names below are
proposals, not approved tags.

| Module candidate | Paperless | Purpose |
| --- | --- | --- |
| 1.3.2-testing.1 | 2.11.4 | Compatibility and backup baseline |
| 1.4.0-testing.1 | 2.20.15 | Required pre-v3 application checkpoint |
| 2.0.0-testing.1 | 3.4.2 | Explicit major transition with v3 behavior changes |

Stable promotion requires separate approval and production validation. The v3
transition is proposed as a module major release because upstream changes search
semantics, task history, scripts and configuration; claiming full behavioral
compatibility within module major 1 would be misleading.

Granian and post-2.17 candidates are test boundaries. Neither upstream source
review nor the uploaded notes establish that each must become a public module
release. Test direct 2.11.4-to-2.20.15 on representative data before choosing.

## Application migration stages (not release approval)

1. Test the Granian boundary using a patched 2.15.x candidate, preserving database
   and helper-service versions initially. Check bind address/port, Traefik headers,
   login redirects, static assets and document downloads.
2. Test a patched post-2.17 version for document `created` date/API semantics and
   scheduled workflow offsets. Decide from migration tests whether a separate
   published intermediate module is necessary.
3. Establish **2.20.15** as the supported pre-v3 checkpoint, with a verified
   database/document backup and restore path. Gate later upgrades on this module
   checkpoint with min-from labels and runtime checks before modifying data.
4. Test v3.4.2 from 2.20.15 only. Block encrypted documents until decrypted; keep
   the original signing key; migrate consumer/OCR/database settings; review custom
   scripts and OIDC/reverse proxy settings. Preserve prior duplicate-handling
   behavior, verify index rebuild/search and CPU requirements. Document unavoidable
   changes such as upstream task-history removal rather than promising no effect.

PostgreSQL major upgrades require their own dump/restore or supported migration
procedure. Refresh compatible patches within a major independently of application
milestones, verifying image tags/digests and supported service versions per stage.

## Supporting-container review

All five existing runtime tags were verified available on Docker Hub. The
released Paperless 3.4.2 compose example uses PostgreSQL 18, Valkey 9, Gotenberg
8.38 and Tika 3.3.1.0; these example major/minor tags are compatibility references,
not fully pinned choices for this module.

Docker Hub currently also offers newer Gotenberg 9 and Tika 4 lines. Do not
substitute those majors merely because they sort newest. Verify the Paperless
integration endpoints and document conversion behavior first. For PostgreSQL,
15.20-bookworm is an available patch candidate within the existing major;
18.7-bookworm is available but needs a separate validated logical restore and
volume-layout migration. PostgreSQL 18's official compose mount is
`/var/lib/postgresql`, unlike the existing `/var/lib/postgresql/data` mount.
Redis 7.2.17-bookworm is an available same-line patch candidate; moving to
Valkey/Redis newer majors requires separate persisted-data/queue tests.

The three-release minimum describes the application path only. A database major
migration or helper-service breaking change can require an additional module
release. The 1.3.2 dependency refresh now selects PostgreSQL 15.20-bookworm, Redis
7.2.16-bookworm, Gotenberg 8.40.0 and Tika 3.3.3.0-full. Database major upgrades
and the other prospective major changes are not enabled at this checkpoint.

## Upgrade guard design requirements

NS8 executes update hooks independently and continues after a failed hook. A
standalone preflight hook that exits nonzero does **not** prevent a later restart
hook from launching migrations. Later stages must couple preflight and restart in
the same checked path, and repeat the guard in application startup before the
container entrypoint can migrate the database. Do not add an isolated failing
hook and claim it blocks upgrades.

`org.nethserver.min-from` and NethForge pins control offered upgrade paths. Direct
administrator CLI updates need the same runtime protection; do not rely on
catalog ordering alone. Record a checkpoint only after the expected application
version is healthy and migrations/data checks have passed. Reject an unverified
or absent pre-v3 checkpoint, encrypted documents, missing original signing keys
and unsupported CPUs before starting v3. Preserve an untouched rollback backup.

No v3 guard or configuration migration is enabled in the compatibility candidate:
its Paperless image remains 2.11.4. The guard must be implemented and tested with
the bridge/v3 changes, including rejected direct jumps and interrupted retries.

## Release and NethForge sequence

For each stage: prepare code and notes, pass fresh-install and previous-stage
upgrade/restore tests, obtain review, run `gh ns8 module-release check`, and request
approval for its exact tag/type before publishing. Never retag a released image.
Only validated stage tags should be added as NethForge pins. Once the final stage
is released, prepare the fork changes in `compgeniuses/ns8-nethforge` and a PR to
`NethServer/ns8-nethforge`, preserving all required bridge releases and image
minimum-version labels. Pin ordering alone does not enforce upgrades.
