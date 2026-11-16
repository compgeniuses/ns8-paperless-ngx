import contextlib
import io
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def state_directory():
    previous = Path.cwd()
    with tempfile.TemporaryDirectory() as directory:
        os.chdir(directory)
        try:
            yield Path(directory)
        finally:
            os.chdir(previous)


def read_env(path):
    return dict(line.split('=', 1) for line in Path(path).read_text().splitlines())


def write_env(path, values):
    Path(path).write_text(''.join(f'{key}={value}\n' for key, value in values.items()))


class StateSafety(unittest.TestCase):
    def test_failed_dump_preserves_last_successful_backup(self):
        def failed_dump(command, stdout, check):
            stdout.write(b'incomplete backup')
            raise subprocess.CalledProcessError(1, command)
        agent = types.SimpleNamespace(read_envfile=lambda path: {})
        with state_directory() as state, patch.dict('sys.modules', agent=agent), patch('subprocess.run', failed_dump):
            (state / 'paperless.pg_dump').write_bytes(b'last successful backup')
            with self.assertRaises(subprocess.CalledProcessError):
                runpy.run_path(str(ROOT / 'imageroot/bin/module-dump-state'))
            self.assertEqual((state / 'paperless.pg_dump').read_bytes(), b'last successful backup')
            self.assertEqual([p.name for p in state.iterdir()], ['paperless.pg_dump'])

    def test_successful_dump_uses_custom_account_and_private_permissions(self):
        def dump(command, stdout, check):
            self.assertIn('custom-user', command)
            self.assertEqual(command[-1], 'custom-db')
            stdout.write(b'complete backup')
        agent = types.SimpleNamespace(read_envfile=lambda path: {'POSTGRES_USER': 'custom-user', 'POSTGRES_DATABASE': 'custom-db'})
        with state_directory() as state, patch.dict('sys.modules', agent=agent), patch('subprocess.run', dump):
            runpy.run_path(str(ROOT / 'imageroot/bin/module-dump-state'))
            self.assertEqual((state / 'paperless.pg_dump').read_bytes(), b'complete backup')
            self.assertEqual((state / 'paperless.pg_dump').stat().st_mode & 0o777, 0o600)

    def test_startup_preserves_original_database_and_signing_key(self):
        agent = types.SimpleNamespace(read_envfile=read_env, write_envfile=write_env)
        files = {'database.env': {'POSTGRES_DATABASE': 'custom-db', 'POSTGRES_USER': 'custom-user', 'POSTGRES_PASSWORD': 'existing-db-secret'},
                 'paperless-db.env': {'PAPERLESS_DBPASS': 'existing-db-secret'},
                 'secret_key.env': {'PAPERLESS_SECRET_KEY': 'existing-signing-key'},
                 'paperless-ngx.env': {'PAPERLESS_ADMIN_PASSWORD': 'existing-admin-secret'}}
        with state_directory() as state, patch.dict('sys.modules', agent=agent):
            for name, values in files.items():
                write_env(name, values)
            before = {name: (state / name).read_bytes() for name in files}
            runpy.run_path(str(ROOT / 'imageroot/bin/discover-database'))
            for name in files:
                self.assertEqual((state / name).read_bytes(), before[name])
                self.assertEqual((state / name).stat().st_mode & 0o777, 0o600)

    def test_missing_signing_key_blocks_startup_without_inventing_credentials(self):
        agent = types.SimpleNamespace(read_envfile=read_env, write_envfile=write_env)
        with state_directory() as state, patch.dict('sys.modules', agent=agent), patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            write_env('database.env', {'POSTGRES_DATABASE': 'custom-db', 'POSTGRES_USER': 'custom-user', 'POSTGRES_PASSWORD': 'original-secret'})
            with self.assertRaises(SystemExit):
                runpy.run_path(str(ROOT / 'imageroot/bin/discover-database'))
            self.assertFalse((state / 'secret_key.env').exists())
            self.assertEqual(read_env('paperless-db.env')['PAPERLESS_DBPASS'], 'original-secret')

    def test_smtp_transport_does_not_depend_on_certificate_verification(self):
        for transport, expected in [('none', ('false', 'false')), ('starttls', ('true', 'false')), ('tls', ('false', 'true'))]:
            for verify in [True, False]:
                with self.subTest(transport=transport, verify=verify), state_directory() as state:
                    settings = {'enabled': True, 'host': 'smtp.example.org', 'port': 587, 'username': 'test-user', 'password': 'test-secret', 'encrypt_smtp': transport, 'tls_verify': verify}
                    agent = types.SimpleNamespace(redis_connect=lambda **kw: None, get_smarthost_settings=lambda r: settings, write_envfile=write_env)
                    with patch.dict('sys.modules', agent=agent), contextlib.redirect_stderr(io.StringIO()):
                        runpy.run_path(str(ROOT / 'imageroot/bin/discover-smarthost'))
                    values = read_env('smarthost.env')
                    self.assertEqual((values['PAPERLESS_EMAIL_USE_TLS'], values['PAPERLESS_EMAIL_USE_SSL']), expected)
                    self.assertEqual(values['PAPERLESS_EMAIL_HOST_PASSWORD'], 'test-secret')
                    self.assertEqual((state / 'smarthost.env').stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
