#!/usr/bin/env python3
"""Reject a skipped checkpoint, including a direct service restart, in CI only."""
import json
import subprocess
import sys
from pathlib import Path
from urllib.request import Request,urlopen


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
    assert guard.returncode != 0 and 'stable module 1.4.0 first' in guard.stderr, guard.stderr
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
    update(module, 'ghcr.io/compgeniuses/paperlessngx:1.4.0')
    def http(path,payload):
        request=Request('http://127.0.0.1'+path,data=json.dumps(payload).encode(),headers={'Host':'paperless.example.org','Content-Type':'application/json',**http_auth})
        with urlopen(request,timeout=60) as response:return json.load(response)
    http_auth={}
    token=http('/api/token/',{'username':'paperlessadmin','password':'Test-only-password-123!'})['token']
    http_auth={'Authorization':'Token '+token}
    parent=http('/api/tags/',{'name':'NS8 hierarchy parent'})
    child=http('/api/tags/',{'name':'NS8 hierarchy child','parent':parent['id']})
    assert child['parent']==parent['id']
    metadata_path=Path('/tmp/paperless-proof-'+module+'.json.metadata.json')
    metadata=json.loads(metadata_path.read_text())
    metadata['tag_hierarchy']={'parent':parent['id'],'child':child['id']}
    metadata_path.write_text(json.dumps(metadata))
    source_schema = fingerprint(module)
    sql = """import agent,subprocess,sys
v=agent.read_envfile('database.env')
subprocess.run(['podman','exec','paperless-pgsql','psql','-XAt','-U',v['POSTGRES_USER'],'-d',v['POSTGRES_DATABASE'],'-v','ON_ERROR_STOP=1','-c',sys.argv[1]],check=True)
"""
    def execute(statement):
        return run('runagent','-m',module,'python3','-c',sql,statement)
    # Change only the disposable fixture's encryption flag; the PDF remains
    # plaintext. The v3 guard must reject it before any migration or restart.
    execute("UPDATE documents_document SET storage_type='gpg' WHERE id=(SELECT min(id) FROM documents_document)")
    try:
        update(module, candidate)
        encrypted = run('runagent','-m',module,'paperless-upgrade','prepare',check=False)
        assert encrypted.returncode != 0 and 'decrypt all encrypted documents' in encrypted.stderr, encrypted.stderr
    finally:
        execute("UPDATE documents_document SET storage_type='unencrypted' WHERE id=(SELECT min(id) FROM documents_document)")
    assert fingerprint(module) == source_schema, 'Rejected encrypted upgrade changed database migrations'
    print('Skipped 1.4.0 checkpoint, direct startup and encrypted documents rejected; required 2.20.15 checkpoint retained')


if __name__ == '__main__':
    main()
