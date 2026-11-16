# Stable 1.3.2 release review

Target: `compgeniuses/ns8-paperless-ngx`, stable **1.3.2**. This is a compatibility
checkpoint with Paperless **2.11.4**, not the final application upgrade.

## Completed checks

- [x] Compatibility and dependency PRs #35 and #36 are merged.
- [x] `gh ns8 module-release check` lists both PRs and no linked issue blockers.
- [x] The published testing.2 image passed QEMU installation, upgrade and full
  NS8/Restic restore on Debian 13 and Rocky 9.
- [x] Nine local state/configuration/backup regression tests passed.
- [x] English/Italian keys and interpolation placeholders match: 54 keys each.
- [x] Detailed, spaced and itemized stable release notes are prepared.
- [x] Minimum NS8 core 3.0.0 and restart/backup/index-maintenance requirements are
  documented.
- [x] Published upstream advisories and the frontend dependency audit were
  reviewed. Findings are documented rather than silently marked resolved.

## Publication checks

- [ ] Merge the release documentation/Italian translation change after its
  relevant checks pass.
- [ ] Publish stable 1.3.2 and verify the tag points to the reviewed main commit.
- [ ] Verify the published stable image and its runtime/minimum-core labels.
- [ ] Attach the CycloneDX SBOM and checksums for the actual published source and
  module image. The inventory scope must be explicit.
- [ ] Update NethForge PR #52 and mark it ready for review without implying that
  unpublished 1.4.0/2.0.x image checks have passed.

## Explicit limitations and follow-up

- [ ] The release-skill criterion "No known exploitable vulnerabilities in the
  release" is **not met** by retaining Paperless 2.11.4. This stable compatibility
  checkpoint proceeds with the disclosed inherited security limitations;
  remediation is part of the later patched application checkpoint. Do not label
  this security review clean or claim that supporting-service updates fix the
  application advisories.
- [ ] UI dependency advisories remain. Preserve the audit evidence and perform
  package remediation and reachability review separately from the compatibility
  checkpoint; do not conflate build-only findings with deployed execution paths.
- [ ] Full populated upgrades from every pre-1.3.1 stable tag have not been
  demonstrated; legacy source review and unit checks have narrower scope.
- [ ] Production-specific schemas, document sets, scripts, mail workflows and
  backup consistency need instance-specific verification.
- [ ] Module 1.4.x must publish the Paperless 2.20.15 checkpoint with
  `org.nethserver.min-from=1.3.2` and tested runtime guards.
- [ ] Module 2.0.x must require the 1.4.0 checkpoint, with
  `org.nethserver.min-from=1.4.0`, tested runtime guards and a validated v3
  migration. Pins preserve visibility and do not enforce direct CLI updates.
- [ ] NethForge reviewers must verify real registry metadata before merging pins
  for unpublished future images. Ready for review does not mean ready to merge.

No linked QA issue exists for this change; workflow evidence is recorded in the
release notes. No issue verification label or manual production test result is
fabricated.
