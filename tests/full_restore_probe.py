#!/usr/bin/env python3
"""Destructive integration test for disposable QEMU instances only.

Back up with NS8/Restic, remove the CI instance, restore into a new instance and
verify original data, document archives, configuration, credentials and Redis.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def command(*args):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # No real credentials are used. Keep diagnostic action errors in CI.
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): {result.stderr[-6000:]}')
    return result.stdout.strip()


def api(action, data):
    output = command('api-cli', 'run', action, '--data', json.dumps(data))
    return json.loads(output) if output else None


def state_hashes(module):
    return command('runagent', '-m', module, 'sh', '-c',
                   'cd "$AGENT_STATE_DIR" && sha256sum database.env secret_key.env paperless-ngx.env')


def main():
    module, result_path = sys.argv[1:]
    if not module.startswith('paperlessngx'):
        raise ValueError('This test is restricted to the disposable Paperless CI module')
    original = state_hashes(module)
    uuid = command('runagent', '-m', module, 'printenv', 'MODULE_UUID')
    assert uuid
    # NS8 checks read access before mkdir. This local destination must exist
    # inside the disposable gateway's persistent volume before validation.
    command('podman', 'exec', 'rclone-gateway', 'mkdir', '-p', '/srv/repo/paperless-ci')
    repository = api('add-backup-repository', {
        'name': 'Paperless disposable CI restore', 'provider': 'rclone', 'url': '',
        'password': 'test-only-restic-password',
        'parameters': {'rclone_conf_secret': 'type = local\n', 'basepath': '/srv/repo/paperless-ci'},
    })['id']
    backup = api('add-backup', {
        'name': 'Paperless disposable CI restore', 'instances': [module], 'repository': repository,
        'schedule': '2099-01-01 00:00:00', 'retention': 1, 'enabled': True,
    })
    # Quiesce the app and Redis only in this test, after all fixture jobs finish.
    # Keep PostgreSQL running for module-dump-state. Pausing avoids systemd
    # Requires= stop propagation, which would otherwise stop the whole pod.
    time.sleep(2)  # Redis appendfsync everysec finishes before the snapshot.
    command('runagent', '-m', module, 'podman', 'pause', 'paperless-server', 'paperless-redis')
    try:
        api('node/1/run-backup', {'id': backup})
    finally:
        command('runagent', '-m', module, 'podman', 'unpause', 'paperless-server', 'paperless-redis')
    snapshots = api('read-backup-snapshots', {'repository': repository, 'path': 'paperlessngx/' + uuid})
    assert snapshots, 'No Restic snapshot was created'
    snapshot = max(snapshots, key=lambda item: item['timestamp'])['id']
    # Delete only the disposable instance after a snapshot exists. This forces
    # restore to reconstruct both media volumes and SQL, without a live fallback.
    command('remove-module', '--no-preserve', module)
    restored = api('restore-module', {'repository': repository, 'path': 'paperlessngx/' + uuid,
                                      'snapshot': snapshot, 'node': 1})['module_id']
    os.umask(0o077)
    Path(result_path).write_text(json.dumps({'module_id': restored}))
    assert state_hashes(restored) == original, 'Configuration or secret file contents changed on restore'
    deadline = time.monotonic() + 120
    while True:
        try:
            command('python3', '/tmp/paperless-probe-' + module + '.py', 'verify', '/tmp/paperless-proof-' + module + '.json')
            command('python3', '/tmp/paperless-probe-' + module + '.py', 'verify', '/tmp/paperless-after-' + module + '.json')
            break
        except RuntimeError:
            if time.monotonic() > deadline:
                raise
            time.sleep(5)
    command('python3', '/tmp/paperless-runtime-' + module + '.py', restored, 'verify')
    print('NS8/Restic restored documents, archives, metadata, configuration, original secrets and Redis into a clean instance')


if __name__ == '__main__':
    main()
