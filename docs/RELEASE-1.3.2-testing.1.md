# Proposed 1.3.2-testing.1 release notes

Status: prepared, not approved or published. Target repository:
`compgeniuses/ns8-paperless-ngx`. Type: testing/prerelease.

This compatibility candidate prepares existing module 1.3.1 installations for a
staged Paperless upgrade. It still runs **Paperless 2.11.4**, PostgreSQL
15.5-bookworm, Redis 7.2.3-bookworm, Gotenberg 8.9.1 and Tika 3.0.0.0-BETA2-full.
It requires **NS8 core 3.0.0 or later**. It is not a production v3 upgrade.

- Preserve omitted settings, custom Paperless options, original database
  credentials, signing keys and existing named volumes. An empty password retains
  the saved value; fresh installations generate one when none is supplied.
- Stop returning the admin password through the reader-accessible configuration
  action. Secret files are private to the module user. Missing original keys or
  credentials must be recovered from backup; startup does not invent replacements.
- Correct SMTP transport discovery, service startup/restart order and restore
  settings. Failed database dumps preserve the last successful dump.
- Add QEMU fresh-install and 1.3.1-upgrade tests with real PDF ingestion, original
  downloads, metadata/secret comparisons and an isolated database restore. Repair
  the frozen UI build, metadata, action schemas and API documentation workflow.

Service restarts are part of configuration and update. SMTP now follows the
central NS8 relay selection; Paperless 2.11.4 always verifies TLS certificates.
Admin account environment variables bootstrap accounts; use Paperless itself to
manage existing account passwords.

Local regression checks, frozen UI installation, lint, production build and
GitHub contract/image/documentation builds pass. QEMU results must be reviewed
before publishing this candidate. A complete NS8 backup restore, older 1.x
layouts and frontend dependency security review remain stable-release gates.

The next proposed application checkpoint is **2.20.15**, required by upstream
before v3. The current final target is **3.4.2**, with a separate module major
release and explicit migration/startup guards. Do not skip that checkpoint.
See [the full audit and upgrade plan](UPGRADE-PLAN.md).
