#!/usr/bin/env python3
"""Read runtime versions and verify disposable Redis persistence markers."""
import json
import subprocess
import sys

MARKER = 'ns8-ci-upgrade-preservation'


def run(module, *command):
    result = subprocess.run(['runagent', '-m', module, *command], text=True, stdout=subprocess.PIPE, check=True)
    return result.stdout.strip()


def main():
    module, operation = sys.argv[1:]
    if operation == 'seed':
        run(module, 'podman', 'exec', 'paperless-redis', 'redis-cli', 'SET', 'ns8-test:upgrade-proof', MARKER)
        run(module, 'podman', 'exec', 'paperless-redis', 'redis-cli', 'RPUSH', 'ns8-test:pending-documents', MARKER)
        run(module, 'podman', 'exec', 'paperless-redis', 'redis-cli', 'SAVE')
    elif operation == 'verify':
        application = run(module, 'podman', 'exec', 'paperless-server', 'python3', '-c',
                          'from paperless.version import __full_version_str__; print(__full_version_str__)')
        assert application == '3.5.0', application
        checkpoint = json.loads(run(module, 'cat', 'upgrades/paperless-checkpoint.json'))
        assert checkpoint['healthy'] is True and checkpoint['application_version'] == application
        assert checkpoint['module_stage'] == '2.0'
        safety = """import agent,json
from pathlib import Path
options=agent.read_envfile('paperless-ngx.env')
assert options['PAPERLESS_DBENGINE']=='postgresql'
assert options['PAPERLESS_OCR_MODE']=='auto'
assert options['PAPERLESS_ARCHIVE_FILE_GENERATION']=='always'
assert options['PAPERLESS_CONSUMER_DELETE_DUPLICATES']=='true'
p=Path('upgrades/paperless-transition.json')
if p.exists() and json.loads(p.read_text()).get('target_application')=='3.5.0':
    history=Path('upgrades/2.0.0/task-history-documents_paperlesstask.jsonl')
    assert history.is_file() and len(history.read_text().splitlines())>=3
print('v3 compatibility defaults and archived legacy task history verified')
"""
        print(run(module, 'python3', '-c', safety))
        assert run(module, 'podman', 'exec', 'paperless-redis', 'redis-cli', '--raw', 'GET', 'ns8-test:upgrade-proof') == MARKER
        assert run(module, 'podman', 'exec', 'paperless-redis', 'redis-cli', '--raw', 'LRANGE', 'ns8-test:pending-documents', '0', '-1') == MARKER
        info = run(module, 'podman', 'exec', 'paperless-redis', 'redis-cli', 'INFO', 'server')
        assert 'redis_version:7.2.16' in info
        command = '''import agent,subprocess
v=agent.read_envfile('database.env')
subprocess.run(['podman','exec','paperless-pgsql','psql','-U',v['POSTGRES_USER'],'-d',v['POSTGRES_DATABASE'],'-Atc','SHOW server_version_num'],check=True)
'''
        pg = run(module, 'python3', '-c', command)
        assert pg == '150020', pg
        command = '''import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:3000/version').read().decode())
print(urllib.request.urlopen('http://127.0.0.1:9998/version').read().decode())
'''
        versions = run(module, 'podman', 'exec', 'paperless-server', 'python3', '-c', command)
        assert '8.40.0' in versions, versions
        # The four-part Docker version identifies Tika Server 3.3.3.
        assert '3.3.3' in versions, versions
        audit = """import agent,subprocess
v=agent.read_envfile('database.env')
sql="SELECT n.nspname, c.relname, am.amname, string_agg(opc.opcname, ',') FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_am am ON am.oid=c.relam CROSS JOIN LATERAL unnest(i.indclass) cl(opcoid) JOIN pg_opclass opc ON opc.oid=cl.opcoid WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%' GROUP BY n.nspname,c.relname,am.amname ORDER BY n.nspname,c.relname"
subprocess.run(['podman','exec','paperless-pgsql','psql','-U',v['POSTGRES_USER'],'-d',v['POSTGRES_DATABASE'],'-Atc',sql],check=True)
"""
        print('PostgreSQL application-index inventory for maintenance review:')
        print(run(module, 'python3', '-c', audit))
        print('PostgreSQL 15.20, Redis 7.2.16, Gotenberg 8.40.0, Tika 3.3.3 verified; Redis key/list retained')
    else:
        raise ValueError(operation)


if __name__ == '__main__':
    main()
