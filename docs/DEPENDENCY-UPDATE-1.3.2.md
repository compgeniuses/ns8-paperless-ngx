# Dependency refresh for module 1.3.2

The compatibility baseline `1.3.2-testing.1` is published and immutable.
This branch prepares **1.3.2-testing.2**, not yet approved or published.
Stable 1.3.2 is not published. Paperless remains **2.11.4** so dependency changes
are evaluated separately from the later application migrations.

## Exact images

All tags were verified on Docker Hub on 2026-11-16, including amd64 and arm64.

| Component | Previous tag | Proposed tag |
| --- | --- | --- |
| PostgreSQL | 15.5-bookworm | 15.20-bookworm |
| Redis | 7.2.3-bookworm | 7.2.16-bookworm |
| Gotenberg | 8.9.1 | 8.40.0 |
| Apache Tika | 3.0.0.0-BETA2-full | 3.3.3.0-full |

No volume names, PostgreSQL major version, passwords, signing keys or document
settings are changed. The existing module update hook restarts every pod member
explicitly; it does not initialize a new database or clear Redis. Container
restarts cause a maintenance interruption; this is not a zero-downtime upgrade.

## PostgreSQL maintenance

[PostgreSQL 15.20 release notes](https://www.postgresql.org/docs/release/15.20/)
state that 15.x does not need dump/restore, but also identify index fixes requiring
review and, where applicable, `REINDEX`. The migration notes refer to earlier
15.x releases as well: review them cumulatively when coming from 15.5. Relevant
examples include unconstrained bpchar btree indexes, gist_trgm_ops indexes,
extension indexes, and potentially affected GIN indexes. A container restart
does not repair an already affected index.

QEMU records the application's index/operator-class inventory for review.
Custom indexes, extensions, collations or logical replication settings need a
separate check against the release notes on the real instance. Do not declare
production approval from a small CI fixture alone. This branch does not silently
run database-wide REINDEX: choose any required repair with a verified backup,
sufficient disk space and an appropriate maintenance window.

## Converter compatibility

[Redis 7.2.16](https://github.com/redis/redis/blob/7.2.16/00-RELEASENOTES)
contains security fixes within the existing 7.2 line. Verify persisted Redis
values and list contents across the upgrade; do not flush the database.

[Gotenberg 8.40.0](https://github.com/gotenberg/gotenberg/releases/tag/v8.40.0)
is the final 8.x release and includes security and behavior changes. It also
updates Chromium and LibreOffice, so rendering must be tested using real Office
and email inputs, not only pre-existing PDFs. Keep the Tika **full** image variant
to preserve its additional parser/OCR dependencies.

## Validation before release

The QEMU update scenario installs 1.3.1, uploads deterministic PDF/DOCX/EML
fixtures, records original/archive hashes, dates/text and secret hashes, and seeds
a Redis key/list. It upgrades through 1.3.2-testing.1 to this candidate and checks
preservation. Fresh-install and update scenarios then verify actual service
versions and convert new Office/email documents using the new helpers.

The full restore test uses NS8's backup configuration, node run-backup action,
Restic snapshots and cluster restore-module action. It pauses only disposable CI
application/Redis containers while capturing the snapshot, removes the original
CI module, restores into a clean module, and verifies document/archive hashes,
configuration, signing/database credentials and Redis markers. This is a test
procedure; it does not alter production backup schedules or instances.

QEMU passed on 2026-11-16 for runtime commit
`74067b50a29ee2077b86c97cd1f8e3241aaa5a7b`: Rocky 9 upgrade passed all 12 tests;
Debian 13 installation passed 11 tests with the upgrade-only test skipped.
Both scenarios passed full NS8/Restic restore, preservation checks and conversion
of new Office/email documents. [Results and artifacts](https://github.com/compgeniuses/ns8-paperless-ngx/actions/runs/43919914773).
The fresh-install schema contained 264 application indexes, all btree, with no
GIN/GiST indexes or unconstrained bpchar operator class in the recorded inventory.
That inventory describes the CI fixture, not every production schema.

A stable release requires separate approval after the outstanding production
validation gates in the upgrade plan are satisfied.

The planned path stays **1.3.1 -> 1.3.2 -> 1.4.x -> 2.0.x**. Module 1.4.x will
require min-from=1.3.2; module 2.0.x will require min-from=1.4.0. The upstream pins
PR is a draft until those stable checkpoint images and their labels are verified.
