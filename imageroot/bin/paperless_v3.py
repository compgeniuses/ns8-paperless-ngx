"""Pure configuration conversions and explicit v3 compatibility checks."""
import fnmatch
import hashlib
import json
import platform
import re
from pathlib import Path

DB_OPTIONS = {
    'PAPERLESS_DBSSLMODE': 'sslmode',
    'PAPERLESS_DBSSLROOTCERT': 'sslrootcert',
    'PAPERLESS_DBSSLCERT': 'sslcert',
    'PAPERLESS_DBSSLKEY': 'sslkey',
    'PAPERLESS_DB_POOLSIZE': 'pool.max_size',
    'PAPERLESS_DB_TIMEOUT': 'connect_timeout',
}


def check_cpu(machine=None, cpuinfo=None):
    machine = machine or platform.machine()
    if machine not in ('x86_64', 'amd64'):
        return
    cpuinfo = Path('/proc/cpuinfo').read_text() if cpuinfo is None else cpuinfo
    flags = [set(value.split()) for value in re.findall(r'^flags\s*:\s*(.*)$', cpuinfo, re.M)]
    required = {'pni', 'ssse3', 'sse4_1', 'sse4_2', 'popcnt', 'cx16', 'lahf_lm'}
    if not flags or any(not required <= value for value in flags):
        raise RuntimeError('Upgrade blocked: Paperless v3 requires an x86-64-v2 CPU; '
                           'migrate to supported hardware before upgrading')


def review_requirements(options, queries, shared_views=None):
    requirements = []
    if any(options.get(key, '').strip() for key in (
            'PAPERLESS_PRE_CONSUME_SCRIPT', 'PAPERLESS_POST_CONSUME_SCRIPT')):
        requirements.append('consume_scripts')
    if options.get('PAPERLESS_CONSUMER_IGNORE_PATTERNS'):
        requirements.append('ignore_patterns')
    providers = json.loads(options.get('PAPERLESS_SOCIALACCOUNT_PROVIDERS') or '{}')
    oidc = providers.get('openid_connect', {})
    if oidc and any(not app.get('settings', {}).get('token_auth_method')
                    for app in oidc.get('APPS', [oidc])):
        requirements.append('oidc')
    explicit = re.compile(r'[\w.]+:(?:"[^"\n]*"|[^\s]+)')
    if any(not explicit.fullmatch(query) for query in queries):
        requirements.append('saved_searches')
    if shared_views:
        requirements.append('shared_saved_views')
    return sorted(requirements)


def review_fingerprint(options, queries, shared_views=None):
    value = json.dumps({'options': options, 'queries': sorted(queries), 'shared_views': shared_views or []}, sort_keys=True,
                       separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def verify_review(options, queries, review, shared_views=None):
    required = review_requirements(options, queries, shared_views)
    fingerprint = review_fingerprint(options, queries, shared_views)
    if required and (review.get('fingerprint') != fingerprint
                     or not set(required) <= set(review.get('acknowledged', []))):
        raise RuntimeError('Upgrade blocked: review v3 compatibility for ' + ', '.join(required)
                           + '; run paperless-upgrade review and acknowledge the reviewed categories')
    return fingerprint


def validate_ocr_arguments(value):
    arguments = json.loads(value) if isinstance(value, str) and value else (value or {})
    if not isinstance(arguments, dict):
        raise RuntimeError('Upgrade blocked: OCR user arguments must be a JSON object')
    if set(arguments) & {'input_file_or_options', 'output_file', 'sidecar'}:
        raise RuntimeError('Upgrade blocked: remove reserved OCR input/output arguments before Paperless 3.5')


def migrate_options(original, legacy=True):
    options = dict(original)
    validate_ocr_arguments(options.get('PAPERLESS_OCR_USER_ARGS'))
    if options.get('PAPERLESS_DBENGINE', 'postgresql') not in ('postgres', 'postgresql'):
        raise RuntimeError('Upgrade blocked: this module requires its PostgreSQL database')
    options['PAPERLESS_DBENGINE'] = 'postgresql'
    # NS8 exposes the pod port on loopback behind one Traefik HTTP proxy.
    options.setdefault('PAPERLESS_ALLAUTH_TRUSTED_PROXY_COUNT', '1')
    old_mode = options.get('PAPERLESS_OCR_MODE', 'skip' if legacy else 'auto')
    modes = {'skip': 'auto', 'skip_noarchive': 'auto',
             'auto': 'auto', 'force': 'force', 'redo': 'redo', 'off': 'off'}
    if old_mode not in modes:
        raise RuntimeError('Upgrade blocked: unsupported OCR mode; review the v3 configuration')
    options['PAPERLESS_OCR_MODE'] = modes[old_mode]
    skip = options.pop('PAPERLESS_OCR_SKIP_ARCHIVE_FILE', None)
    archives = {'never': 'always', 'with_text': 'auto', 'always': 'never'}
    if skip is not None and skip not in archives:
        raise RuntimeError('Upgrade blocked: unsupported legacy archive setting')
    default_archive = archives[skip] if skip else ('never' if old_mode == 'skip_noarchive' else 'always')
    options.setdefault('PAPERLESS_ARCHIVE_FILE_GENERATION', default_archive)
    if options['PAPERLESS_ARCHIVE_FILE_GENERATION'] not in ('auto', 'always', 'never'):
        raise RuntimeError('Upgrade blocked: unsupported v3 archive setting')
    if legacy:
        # v2 always rejected duplicate documents. Its false value only kept the
        # input file; v3 false would instead allow duplicate documents.
        options['PAPERLESS_CONSUMER_DELETE_DUPLICATES'] = 'true'
    else:
        options.setdefault('PAPERLESS_CONSUMER_DELETE_DUPLICATES', 'true')
    polling = options.pop('PAPERLESS_CONSUMER_POLLING', '0')
    options.setdefault('PAPERLESS_CONSUMER_POLLING_INTERVAL', polling)
    delay = options.get('PAPERLESS_CONSUMER_POLLING_DELAY', '5') if float(options['PAPERLESS_CONSUMER_POLLING_INTERVAL']) > 0 else options.get('PAPERLESS_CONSUMER_INOTIFY_DELAY', '0.5')
    options.setdefault('PAPERLESS_CONSUMER_STABILITY_DELAY', delay)
    for key in ['PAPERLESS_CONSUMER_POLLING_DELAY', 'PAPERLESS_CONSUMER_POLLING_RETRY_COUNT',
                'PAPERLESS_CONSUMER_INOTIFY_DELAY', 'PAPERLESS_CONSUMER_BARCODE_SCANNER']:
        options.pop(key, None)
    if legacy and options.get('PAPERLESS_CONSUMER_IGNORE_PATTERNS'):
        patterns = json.loads(options['PAPERLESS_CONSUMER_IGNORE_PATTERNS'])
        if not isinstance(patterns, list) or not all(isinstance(pattern, str) for pattern in patterns):
            raise RuntimeError('Upgrade blocked: ignore patterns must be a JSON array of strings')
        options['PAPERLESS_CONSUMER_IGNORE_PATTERNS'] = json.dumps([fnmatch.translate(pattern) for pattern in patterns])
    advanced = {}
    if options.get('PAPERLESS_DB_OPTIONS'):
        for item in options['PAPERLESS_DB_OPTIONS'].split(','):
            key, value = item.split('=', 1)
            advanced[key.strip()] = value.strip()
    for old, new in DB_OPTIONS.items():
        if old in options:
            value = options.pop(old)
            if ',' in value or '\n' in value:
                raise RuntimeError('Upgrade blocked: migrate the advanced database option explicitly')
            advanced.setdefault(new, value)
    if advanced:
        options['PAPERLESS_DB_OPTIONS'] = ','.join(key + '=' + value for key, value in sorted(advanced.items()))
    return options
