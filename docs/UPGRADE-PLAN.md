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

Proposed NS8 tag: **1.3.2-testing.1**, not yet approved or published.

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

Seven regression tests pass, covering partial configuration, secret non-disclosure,
failed/successful backup replacement, original credentials and signing-key
preservation, and SMTP transport selection. Python/JSON/bash syntax and
`git diff --check` pass. The frozen UI install and production build pass with
existing lint, browser-data and bundle-size warnings. GitHub contract, image
and API documentation builds pass. QEMU install/update validation is running;
record its final results before publishing. The first run exposed a test parser
issue (`add-module` prints a Python literal rather than JSON); the parser now
uses `ast.literal_eval`, and the corrected suite must pass before release.

The new minimum-core label requires NS8 core 3.0.0 or later; check the actual
production nodes before offering this candidate. Older nodes need an independently
validated core update first.

## Remaining conformity/production validation

The first candidate is not production approved. QEMU must prove fresh install,
existing 1.3.1 upgrade, document consumption/download/search, authentication,
backup/restore and repeat configuration. The Robot coverage exercises ingestion, document/secret preservation and
a populated database restore. It does not yet prove a complete NS8 Restic
restore with matching media volumes.

Before a stable baseline release, also complete:

- Complete the frontend dependency security audit. Upgrade UI packages
  separately after the baseline.
- Restore a populated backup into a clean instance, including original signing
  key and custom settings; determine whether document consumption must be paused
  for a consistent database/document snapshot.
- Test upgrade hooks against every supported 1.x layout; do not claim one minor
  version can skip required migrations merely because its image starts.
- Add the repository `ns8` topic: the connected GitHub installation returned
  HTTP 403 for repository-topic administration, so this remains a maintainer
  action. Verify forge logo/screenshot/metadata quality when updating NethForge.

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
release. Choose exact helper tags and digests only after the baseline passes;
none of these prospective dependency updates is enabled here.

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
