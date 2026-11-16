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
  and download a real PDF, compare text/dates and preserve original secret files.
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
existing lint, browser-data and bundle-size warnings. QEMU has not yet run.

The new minimum-core label requires NS8 core 3.0.0 or later; check the actual
production nodes before offering this candidate. Older nodes need an independently
validated core update first.

## Remaining conformity/production validation

The first candidate is not production approved. QEMU must prove fresh install,
existing 1.3.1 upgrade, document consumption/download/search, authentication,
backup/restore and repeat configuration. The current Robot coverage is an initial
smoke test, not proof of document-level migration or restore correctness.

Before a stable baseline release, also complete:

- Complete the frontend dependency security audit. Upgrade UI packages
  separately after the baseline.
- Restore a populated backup into a clean instance, including original signing
  key and custom settings; determine whether document consumption must be paused
  for a consistent database/document snapshot.
- Test upgrade hooks against every supported 1.x layout; do not claim one minor
  version can skip required migrations merely because its image starts.
- Verify repository topics and forge logo/screenshot/metadata quality separately.

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

## Release and NethForge sequence

For each stage: prepare code and notes, pass fresh-install and previous-stage
upgrade/restore tests, obtain review, run `gh ns8 module-release check`, and request
approval for its exact tag/type before publishing. Never retag a released image.
Only validated stage tags should be added as NethForge pins. Once the final stage
is released, prepare the fork changes in `compgeniuses/ns8-nethforge` and a PR to
`NethServer/ns8-nethforge`, preserving all required bridge releases and image
minimum-version labels. Pin ordering alone does not enforce upgrades.
