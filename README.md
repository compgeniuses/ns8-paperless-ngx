# Paperless-ngx for NethServer 8

Paperless-ngx transforms scanned and digital documents into a searchable archive.
This rootless NS8 module runs Paperless, PostgreSQL, Redis, Apache Tika and
Gotenberg in one pod, behind the node's Traefik proxy.

## Installation and configuration

Select an approved stable tag from [Releases](https://github.com/compgeniuses/ns8-paperless-ngx/releases).
Replace `VERSION` with that tag; do not use a development branch in production.

```sh
add-module ghcr.io/compgeniuses/paperlessngx:VERSION 1
```

Use the returned module ID in subsequent commands, for example `paperlessngx1`.
Configure a DNS name pointing to the node:

```sh
api-cli run module/paperlessngx1/configure-module --data '{
  "host": "paperless.example.org",
  "lets_encrypt": false,
  "http2https": true,
  "paperless_name": "Paperless",
  "PAPERLESS_ADMIN_USER": "paperlessadmin",
  "PAPERLESS_ADMIN_PASSWORD": "<choose-a-unique-password>",
  "PAPERLESS_TIME_ZONE": "UTC",
  "PAPERLESS_OCR_LANGUAGE": "eng"
}'
```

`host` is required. `lets_encrypt` and `http2https` default to true on first
configuration and retain their saved values when omitted later. Enable Let's
Encrypt only when the hostname is publicly resolvable and certificate issuance
is available. The existing default timezone is `America/Los_Angeles`.

Other supported inputs are `PAPERLESS_ADMIN_MAIL`, `PAPERLESS_COOKIE_PREFIX` and
`PAPERLESS_FILENAME_FORMAT`. Omitted settings and additional options already
stored in `state/paperless-ngx.env` are retained. Historical database, PHP,
`PAPERLESS_URL` and Tika configure inputs remain accepted for compatibility but
are ignored: the module manages these settings internally.

An empty or omitted admin password preserves the existing saved value. On first
setup, supply a password or retrieve the randomly generated one as the module
administrator from the protected `state/paperless-ngx.env` file. Paperless's admin
environment settings bootstrap an account; manage existing account passwords
within Paperless. `get-configuration` always returns an empty password. Do not
attach environment files or database dumps to public issues.

The application is served at the configured hostname, for example
`https://paperless.example.org/`. It does not use a `/paperlessngx/` subpath.
Tika and Gotenberg are enabled for Office documents and email conversion.

## Email

The application discovers the centralized NS8 smarthost each time its service
starts. A `smarthost-changed` event restarts only the Paperless application to
refresh its effective mail settings. Centrally managed mail variables take
precedence over stale values written by previous module versions.

Transport choices map to plain SMTP, STARTTLS or implicit TLS. Paperless 2.11.4
always verifies TLS certificates; NS8's `tls_verify=false` cannot be applied to
this application. Use a relay certificate trusted by the container. A disabled
smarthost clears the relay credentials and restores localhost SMTP defaults.

## Backup, restore and upgrades

NS8 backups include a PostgreSQL dump, Paperless document/data/export/consume
volumes, Redis data and the original configuration and secret files. A failed
database dump does not replace the last successful dump. A readable dump alone
does not prove a consistent document snapshot: validate a populated restore
before relying on it for an application migration.

Never regenerate a missing signing key or guess database credentials on an
existing installation. Restore the original files from backup. Existing volume
names and database/signing credentials are retained by this compatibility change.

See [the conformity audit and staged upgrade plan](docs/UPGRADE-PLAN.md).
The first compatibility candidate retains Paperless **2.11.4** and the existing
runtime dependency versions. It is not a v3 upgrade or a production-approved
release. Upstream requires **2.20.15** before v3. Rollback after database migration
requires restoring matching database and document volumes; changing an image
back is insufficient.

## Tests and continuous integration

[Test module](.github/workflows/test-module.yml) uses the standard NS8 QEMU
workflow on Rocky Linux 9 and Debian 13. The image name is explicitly
`paperlessngx`, since it differs from the repository suffix. The install scenario
uses the branch image; the update scenario installs module 1.3.1 first, configures
it, ingests a real PDF, updates to the branch image and verifies original-file
bytes, document content/dates, login and secret-file preservation. Both scenarios
check Traefik, partial configuration and a readable database dump.

Run it from GitHub Actions using **Run workflow**, selecting the branch to test.
The shared runner provides Robot Framework and SSH dependencies. The removed
DigitalOcean-specific/local runner is not required.

Fast local regression checks:

```sh
python3 -m unittest discover -s .tests -v
bash -n build-images.sh
```

The UI uses the pinned Node builder from `build-images.sh` and a frozen Yarn
lockfile. Update translations only in `ui/public/i18n/en/translation.json`; other
language files are maintained by the translation workflow.

## Uninstall

```sh
remove-module --no-preserve paperlessngx1
```

This removes the instance and its data. Keep a verified backup before removal.

## References

- [Paperless documentation](https://docs.paperless-ngx.com/)
- [Module issues](https://github.com/compgeniuses/ns8-paperless-ngx/issues)
- [NethServer module skills](https://github.com/NethServer/agents/tree/main/skills/nethserver-ns8-module)
