import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class UpgradeCheckpoints(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)
        loader = importlib.machinery.SourceFileLoader('v3_upgrade_test', str(ROOT / 'imageroot/bin/paperless-upgrade'))
        self.module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        with patch.dict('sys.modules', agent=types.SimpleNamespace(read_envfile=lambda p: {})), patch.object(sys, 'path', [str(ROOT / 'imageroot/bin'), *sys.path]):
            loader.exec_module(self.module)
        self.module.STATE = self.state
        self.cpu = patch.object(self.module, 'check_cpu')
        self.cpu.start()
        self.addCleanup(self.cpu.stop)

    def source(self):
        return {'module_stage': '1.4', 'application_version': '2.20.15', 'healthy': True,
                'migration_fingerprint': 'source-schema', 'module_image': 'ghcr.io/compgeniuses/paperlessngx:1.4.0'}

    def test_missing_checkpoint_blocks_even_a_claimed_previous_version(self):
        with patch.dict(os.environ, PREV_IMAGE_URL='ghcr.io/compgeniuses/paperlessngx:1.4.0'):
            with self.assertRaisesRegex(RuntimeError, 'stable module 1.4.0'):
                self.module.preflight(prepare=True)

    def test_unverified_or_wrong_application_cannot_be_a_v3_source(self):
        source = self.source()
        self.assertTrue(self.module.allowed_source_checkpoint(source))
        source['application_version'] = '2.20.14'
        self.assertFalse(self.module.allowed_source_checkpoint(source))
        source['application_version'] = '2.20.15'
        source['healthy'] = False
        self.assertFalse(self.module.allowed_source_checkpoint(source))

    def test_later_v3_data_cannot_be_downgraded(self):
        source = {'module_stage': '2.1', 'application_version': '3.5.0', 'healthy': True}
        self.assertFalse(self.module.allowed_source_checkpoint(source))

    def test_checkpoint_rejects_a_mismatched_database_schema(self):
        self.module.write_json('paperless-checkpoint.json', {'module_stage': '2.0', 'application_version': '3.4.2', 'healthy': True, 'migration_fingerprint': 'original'})
        with patch.object(self.module, 'wait_database'), patch.object(self.module, 'migration_fingerprint', return_value='changed'):
            with self.assertRaisesRegex(RuntimeError, 'database no longer matches'):
                self.module.preflight()

    def test_transition_requires_the_original_backup(self):
        self.module.write_json('paperless-transition.json', {'target_application': '3.4.2', 'source_checkpoint': self.source(), 'backup_complete': True})
        with self.assertRaisesRegex(RuntimeError, 'backup is missing or changed'):
            self.module.preflight()

    def test_changed_configuration_invalidates_prepared_transition(self):
        directory = self.state / 'upgrades/2.0.0'
        directory.mkdir(parents=True)
        (directory / 'paperless.pg_dump').write_bytes(b'complete')
        self.module.write_json('paperless-transition.json', {'target_application': '3.4.2', 'source_checkpoint': self.source(), 'backup_complete': True, 'backup_sha256': hashlib.sha256(b'complete').hexdigest(), 'target_configuration_fingerprint': 'original'})
        with patch.object(self.module, 'configuration_fingerprint', return_value='changed'):
            with self.assertRaisesRegex(RuntimeError, 'configuration changed'):
                self.module.preflight()

    def test_failed_dump_unpauses_without_authorizing_migration(self):
        calls = []
        def run(*command, **kwargs):
            calls.append(command)
            if command[0] == 'module-dump-state':
                raise RuntimeError('failed dump')
            return 'false' if '{{.State.Paused}}' in command else 'true'
        with patch.object(self.module, 'recover_preparation'), patch.object(self.module, 'recover_freeze'), patch.object(self.module, 'preflight', return_value='source'), patch.object(self.module, 'wait_database'), patch.object(self.module, 'run', run):
            with self.assertRaisesRegex(RuntimeError, 'failed dump'):
                self.module.prepare_update()
        self.assertIn(('podman', 'unpause', 'paperless-server'), calls)
        self.assertFalse(self.module.read_json('paperless-transition.json'))

    def test_interrupted_configuration_is_restored_before_retry(self):
        directory = self.state / 'upgrades/2.0.0'
        directory.mkdir(parents=True)
        (directory / 'paperless.pg_dump').write_bytes(b'complete')
        for name in ['paperless-ngx.env', 'paperless-db.env']:
            (directory / name).write_text('original settings')
            (self.state / name).write_text('half-converted settings')
        self.module.write_json('paperless-v3-preparation.json', {'source_fingerprint': 'source-schema', 'backup_sha256': hashlib.sha256(b'complete').hexdigest()})
        with patch.object(self.module, 'source_checkpoint', return_value=self.source()):
            self.module.recover_preparation()
        for name in ['paperless-ngx.env', 'paperless-db.env']:
            self.assertEqual((self.state / name).read_text(), 'original settings')
        self.assertFalse(self.module.read_json('paperless-v3-preparation.json'))

    def test_interrupted_copy_does_not_leave_a_partial_backup(self):
        source = self.state / 'source'; source.write_bytes(b'complete')
        target = self.state / 'target'
        def failed_copy(source, temporary):
            Path(temporary).write_bytes(b'partial')
            raise OSError('interrupted')
        with patch.object(self.module.shutil, 'copy2', failed_copy):
            with self.assertRaises(OSError):
                self.module.atomic_copy(source, target)
        self.assertFalse(target.exists())
        self.assertFalse(list(self.state.glob('target.*.tmp')))

    def test_own_interrupted_freeze_is_recovered(self):
        self.module.write_json('paperless-freeze.json', {'target_application': '3.4.2'})
        calls=[]
        with patch.object(self.module, 'run', side_effect=lambda *args, **kw: calls.append(args) or 'true'):
            self.module.recover_freeze()
        self.assertIn(('podman', 'unpause', 'paperless-server'), calls)
        self.assertEqual(self.module.read_json('paperless-freeze.json'), {})

    def test_encrypted_documents_are_rejected_before_preparation(self):
        with patch.object(self.module, 'sql', return_value='1'):
            with self.assertRaisesRegex(RuntimeError, 'decrypt all encrypted documents'):
                self.module.validate_v3_source({})
        self.assertFalse(list(self.state.iterdir()))

    def test_mail_rule_clamping_requires_review_instead_of_silent_data_change(self):
        with patch.object(self.module, 'sql', side_effect=['0', '32768']):
            with self.assertRaisesRegex(RuntimeError, 'maximum_age greater than 32767'):
                self.module.validate_v3_source({})
        self.assertFalse(list(self.state.iterdir()))

    def test_fresh_marker_cannot_authorize_an_existing_application_schema(self):
        self.module.write_json('paperless-fresh.json', {'application_version': '3.4.2'})
        with patch.object(self.module, 'wait_database'), patch.object(self.module, 'sql', return_value='20'):
            with self.assertRaisesRegex(RuntimeError, 'stable module 1.4.0'):
                self.module.preflight()
