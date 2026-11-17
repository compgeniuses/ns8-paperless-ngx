#!/usr/bin/env python3
"""Reject a skipped checkpoint, including a direct service restart, in CI only."""
import json
import subprocess
import sys


def run(*args, check=True):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} failed: {result.stderr[-3000:]}')
    return result


def fingerprint(module):
    script = '''import agent,subprocess
v=agent.read_envfile('database.env')
sql="SELECT md5(string_agg(app || '.' || name, ',' ORDER BY app, name)) FROM django_migrations"
subprocess.run(['podman','exec','paperless-pgsql','psql','-XAt','-U',v['POSTGRES_USER'],'-d',v['POSTGRES_DATABASE'],'-c',sql],check=True)
'''
    return run('runagent', '-m', module, 'python3', '-c', script).stdout.strip()


def update(module, image):
    run('api-cli', 'run', 'update-module', '--data', json.dumps({
        'force': True, 'module_url': image, 'instances': [module]}))


def main():
    module, candidate = sys.argv[1:]
    original = fingerprint(module)
    update(module, candidate)
    guard = run('runagent', '-m', module, 'paperless-upgrade', 'check', check=False)
    assert guard.returncode != 0 and 'stable module 1.3.2 first' in guard.stderr, guard.stderr
    # The core does not propagate a failed update hook. The service entrypoint
    # must independently reject startup before any upstream migration runs.
    restarted = run('runagent', '-m', module, 'systemctl', '--user', 'restart',
                    'paperless-server.service', check=False)
    assert restarted.returncode != 0, 'Direct startup unexpectedly bypassed the checkpoint'
    # Restore only the disposable CI module to the required baseline. A failed
    # dependency can stop the pod, so explicitly reset/start it via configure.
    update(module, 'ghcr.io/compgeniuses/paperlessngx:1.3.2')
    run('runagent', '-m', module, 'systemctl', '--user', 'reset-failed')
    run('api-cli', 'run', 'module/' + module + '/configure-module', '--data', json.dumps({
        'host': 'paperless.example.org', 'http2https': False, 'lets_encrypt': False}))
    assert fingerprint(module) == original, 'A rejected jump changed the database migrations'
    print('Skipped 1.3.2 checkpoint and direct startup rejected; baseline restored without database migrations')


if __name__ == '__main__':
    main()
