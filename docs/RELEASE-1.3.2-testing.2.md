# Proposed 1.3.2-testing.2

Status: prepared, not approved or published. Testing release for
`compgeniuses/ns8-paperless-ngx`.

Keep Paperless at **2.11.4** and refresh supporting services to PostgreSQL
**15.20-bookworm**, Redis **7.2.16-bookworm**, Gotenberg **8.40.0** and Apache
Tika **3.3.3.0-full**. Preserve existing volumes, credentials and application
configuration. No PostgreSQL major-version or Paperless application migration
is included. Existing instances restart during the update.

Extend QEMU coverage with real DOCX/email conversion, original/archive file
preservation, Redis key/list persistence, running-version checks and a complete
NS8/Restic module restore into a clean instance. The update scenario covers
1.3.1 -> 1.3.2-testing.1 -> this candidate.

PostgreSQL 15.20's index-maintenance notes must be reviewed for the actual
instance, including applicable earlier 15.x fixes. No silent database-wide
REINDEX is performed. See [dependency compatibility and maintenance notes](DEPENDENCY-UPDATE-1.3.2.md).

Validation results are pending. This candidate is not stable or production
approved. Do not modify or retag the published 1.3.2-testing.1 release.
