import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class UpgradeCheckpoints(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state = Path(self.temporary.name)
        loader = importlib.machinery.SourceFileLoader('paperless_upgrade_test', str(ROOT / 'imageroot/bin/paperless-upgrade'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', agent=types.SimpleNamespace(read_envfile=lambda p: {})):
            loader.exec_module(self.module)
        self.module.STATE = self.state

    def test_only_the_required_stable_paperless_source_is_accepted(self):
        for value in ['ghcr.io/compgeniuses/paperlessngx:1.3.2', 'ghcr.io/compgeniuses/paperlessngx:1.4.1']:
            self.assertTrue(self.module.valid_source(value))
        for value in ['', 'ghcr.io/compgeniuses/paperlessngx:1.3.1',
                      'ghcr.io/compgeniuses/paperlessngx:1.3.2-testing.2',
                      'ghcr.io/compgeniuses/paperlessngx:2.0.0', 'unrelated:1.3.2']:
            self.assertFalse(self.module.valid_source(value), value)

    def test_source_version_cannot_bypass_the_startup_backup_guard(self):
        with patch.dict(os.environ, PREV_IMAGE_URL='ghcr.io/compgeniuses/paperlessngx:1.3.2'):
            self.assertEqual(self.module.preflight(prepare=True), 'source')
            with self.assertRaisesRegex(RuntimeError, 'Upgrade blocked'):
                self.module.preflight()

    def test_failed_backup_unpauses_original_app_and_does_not_authorize_migration(self):
        calls = []
        def run(*command, **kwargs):
            calls.append(command)
            if command[0] == 'module-dump-state':
                raise RuntimeError('dump failed')
            return 'true'
        with patch.dict(os.environ, PREV_IMAGE_URL='ghcr.io/compgeniuses/paperlessngx:1.3.2'), \
                patch.object(self.module, 'wait_database'), patch.object(self.module, 'run', run):
            with self.assertRaisesRegex(RuntimeError, 'dump failed'):
                self.module.prepare_update()
        self.assertIn(('podman', 'unpause', 'paperless-server'), calls)
        self.assertFalse((self.state / 'upgrades/paperless-transition.json').exists())

    def test_successful_preparation_preserves_first_backup_and_original_timestamps(self):
        (self.state / 'paperless.pg_dump').write_bytes(b'original populated dump')
        def run(*command, **kwargs):
            return 'false' if command[:2] == ('podman', 'inspect') else ''
        original = '{"id":1,"created":"2024-01-02T12:34:56+00:00"}'
        with patch.dict(os.environ, PREV_IMAGE_URL='ghcr.io/compgeniuses/paperlessngx:1.3.2'), \
                patch.object(self.module, 'wait_database'), patch.object(self.module, 'run', run), \
                patch.object(self.module, 'sql', return_value=original):
            self.module.prepare_update()
            (self.state / 'paperless.pg_dump').write_bytes(b'later dump')
            self.module.prepare_update()
        directory = self.state / 'upgrades/1.4.0'
        self.assertEqual((directory / 'paperless.pg_dump').read_bytes(), b'original populated dump')
        self.assertEqual((directory / 'original-created-timestamps.jsonl').read_text(), original + '\n')
        self.assertEqual((directory / 'paperless.pg_dump').stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.module.preflight(), 'transition')

    def test_fresh_install_marker_does_not_authorize_a_populated_legacy_restore(self):
        self.module.write_json('paperless-fresh.json', {'application_version': self.module.APP_VERSION})
        with patch.object(self.module, 'wait_database'), patch.object(self.module, 'sql', return_value='5'):
            with self.assertRaisesRegex(RuntimeError, 'Upgrade blocked'):
                self.module.preflight()

    def test_checkpoint_rejects_a_mismatched_database_schema(self):
        self.module.write_json('paperless-checkpoint.json', {
            'module_stage': '1.4', 'application_version': '2.20.15',
            'healthy': True, 'migration_fingerprint': 'original-schema',
        })
        with patch.object(self.module, 'wait_database'), patch.object(self.module, 'migration_fingerprint', return_value='other-schema'):
            with self.assertRaisesRegex(RuntimeError, 'database no longer matches'):
                self.module.preflight()

    def test_wrong_version_transition_never_authorizes_startup(self):
        self.module.write_json('paperless-transition.json', {
            'target_application': '3.4.2', 'source_image': 'ghcr.io/compgeniuses/paperlessngx:1.3.2',
            'backup_complete': True,
        })
        with self.assertRaisesRegex(RuntimeError, 'Upgrade blocked'):
            self.module.preflight()
