# Administrator review for the v3 transition

Normal installations without the listed compatibility conditions upgrade from a
verified 1.4.0 checkpoint automatically. The guard stops cases that require an
administrator decision before application migrations run.

NS8 can report update-hook completion despite a failed hook. Check the module
log and actual application health: a blocked guard deliberately keeps the old
application running when possible. Do not force a service restart or delete the
checkpoint/backup files to bypass it.

## Resolve hard blockers

- Upgrade through stable 1.3.2 and then stable 1.4.0. The running application must
  have reached healthy 2.20.15, with a matching checkpoint/schema fingerprint.
- Migrate unsupported x86 hardware to a host meeting the x86-64-v2 baseline.
- Decrypt legacy encrypted documents on 2.20.15 and verify their downloads before
  retrying. The upstream command is `decrypt_documents`; run it in the existing
  application container with the original passphrase and a verified backup.
- Remove the legacy passphrase setting after confirming no encrypted documents
  remain. Do not rotate the original application signing key.
- Review and explicitly adjust mail-rule maximum ages above 32767; the module
  does not silently truncate those values.

These conditions cannot be bypassed by a review acknowledgement.

## Review custom behavior

Update custom consume scripts to use `DOCUMENT_SOURCE_PATH`, `DOCUMENT_ID` and
the other documented `DOCUMENT_*` variables, rather than positional arguments.
These variables also work on 2.20.15, so scripts can be updated before migration.

Check custom consumer ignore rules against the new regex semantics and additive
upstream defaults. The module converts reviewed glob expressions, but conversion
does not remove v3's built-in ignores.

Change saved searches that depended on implicit note/custom-field matches to
explicit field queries. Upstream migrates explicit old prefixes automatically;
ambiguous unqualified rules require review.

For OIDC applications, configure the intended `token_auth_method` in each
provider application's settings. Preserve an explicitly configured proxy count
when the deployment has more HTTP hops than the module's Traefik proxy.

## Inspect and acknowledge the exact configuration

After the 2.0.0 module code is installed but its guard has blocked a custom case,
the old application remains at 2.20.15. The new safety helper is available:

```bash
runagent -m paperlessngx1 paperless-upgrade review
```

Replace `paperlessngx1` with the actual module ID. The command prints a
configuration/query fingerprint and the categories requiring review; it does
not print secret values.

After reviewing the actual scripts/settings/searches, acknowledge the returned
fingerprint and only the categories you have reviewed:

```bash
runagent -m paperlessngx1 paperless-upgrade acknowledge FINGERPRINT consume_scripts ignore_patterns saved_searches
```

Use the actual fingerprint and returned category names; `oidc` is another
possible category. The helper rejects an incomplete acknowledgement or an old
fingerprint. A later change to the configuration or relevant queries invalidates
the acknowledgement.

Retry the module update after resolving all conditions. Preparation writes a
verified database/configuration backup, archives legacy task history, converts
the settings and authorizes the new container entrypoint. An interrupted
configuration conversion is recovered from the original copies before retrying.

## Recovery files

The protected `upgrades/` directory in module state contains checkpoint and
transition receipts plus versioned database/configuration recovery files. The
1.4.0 directory retains original document-created timestamps; the 2.0.0 directory
retains the pre-v3 dates and legacy task-history exports. These files are included
in NS8/Restic backup and should be kept until the complete migration and the
application integrations are verified.
