#!/bin/bash
# Run only on the disposable QEMU test module after ingesting the proof PDF.
set -euo pipefail
cd "$AGENT_STATE_DIR"
test -s paperless.pg_dump
scratch=$(mktemp -d "$AGENT_STATE_DIR/restore-check.XXXXXX")
check_name="paperless-restore-check-${MODULE_ID}"
cleanup() {
    podman rm --force --ignore --volumes "$check_name" >/dev/null
    rm -rf "$scratch"
}
trap cleanup EXIT
mkdir "$scratch/initdb"
cp paperless.pg_dump "$scratch/backup.pg_dump"
# Non-executable .sh is sourced by the PostgreSQL entrypoint, making its
# docker_temp_server_stop helper available after initialization and restore.
cat > "$scratch/initdb/check.sh" <<'EOS'
set -e
pg_restore --exit-on-error --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB" /backup.pg_dump
count=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM documents_document WHERE title = 'NS8 upgrade preservation proof';")
test "$count" = 1
docker_temp_server_stop
exit 0
EOS
chmod 755 "$scratch/initdb"
chmod 644 "$scratch/initdb/check.sh" "$scratch/backup.pg_dump"
# A disposable anonymous volume isolates restored database files from the live
# postgres-data volume. --rm also removes the anonymous volume on success/failure.
# The live PostgreSQL service is never stopped or modified by this test.
podman run --rm --interactive --network=none --name "$check_name" \
    --env-file="$AGENT_STATE_DIR/database.env" \
    --env "POSTGRES_DB=$(python3 -c 'import agent; print(agent.read_envfile("database.env")["POSTGRES_DATABASE"])')" \
    --volume=/var/lib/postgresql/data \
    --volume="$scratch/initdb:/docker-entrypoint-initdb.d:ro,Z" \
    --volume="$scratch/backup.pg_dump:/backup.pg_dump:ro,Z" \
    "$POSTGRES_IMAGE" < /dev/null
