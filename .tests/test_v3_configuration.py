import fnmatch
import importlib.util
import json
from pathlib import Path
import re
import unittest

path = Path(__file__).resolve().parents[1] / 'imageroot/bin/paperless_v3.py'
spec = importlib.util.spec_from_file_location('v3_config_tests', path)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)


class V3Configuration(unittest.TestCase):
    def test_legacy_defaults_preserve_archives_and_duplicate_rejection(self):
        result = v3.migrate_options({})
        self.assertEqual(result['PAPERLESS_OCR_MODE'], 'auto')
        self.assertEqual(result['PAPERLESS_ARCHIVE_FILE_GENERATION'], 'always')
        self.assertEqual(result['PAPERLESS_CONSUMER_DELETE_DUPLICATES'], 'true')
        self.assertEqual(result['PAPERLESS_DBENGINE'], 'postgresql')
        self.assertEqual(result['PAPERLESS_CONSUMER_STABILITY_DELAY'], '0.5')

    def test_explicit_legacy_ocr_archive_preferences_are_preserved(self):
        for old, expected in [('never', 'always'), ('with_text', 'auto'), ('always', 'never')]:
            result = v3.migrate_options({'PAPERLESS_OCR_SKIP_ARCHIVE_FILE': old})
            self.assertEqual(result['PAPERLESS_ARCHIVE_FILE_GENERATION'], expected)
            self.assertNotIn('PAPERLESS_OCR_SKIP_ARCHIVE_FILE', result)
        self.assertEqual(v3.migrate_options({'PAPERLESS_OCR_MODE': 'skip_noarchive'})['PAPERLESS_ARCHIVE_FILE_GENERATION'], 'never')

    def test_old_false_means_reject_duplicates_but_new_explicit_false_is_respected(self):
        original = {'PAPERLESS_CONSUMER_DELETE_DUPLICATES': 'false'}
        self.assertEqual(v3.migrate_options(original)['PAPERLESS_CONSUMER_DELETE_DUPLICATES'], 'true')
        self.assertEqual(v3.migrate_options(original, legacy=False)['PAPERLESS_CONSUMER_DELETE_DUPLICATES'], 'false')
        self.assertEqual(original['PAPERLESS_CONSUMER_DELETE_DUPLICATES'], 'false')

    def test_polling_and_stability_settings_are_converted(self):
        result = v3.migrate_options({'PAPERLESS_CONSUMER_POLLING': '3', 'PAPERLESS_CONSUMER_POLLING_DELAY': '7', 'PAPERLESS_CONSUMER_POLLING_RETRY_COUNT': '9'})
        self.assertEqual(result['PAPERLESS_CONSUMER_POLLING_INTERVAL'], '3')
        self.assertEqual(result['PAPERLESS_CONSUMER_STABILITY_DELAY'], '7')
        self.assertNotIn('PAPERLESS_CONSUMER_POLLING_RETRY_COUNT', result)

    def test_glob_conversion_matches_the_original_filename_policy(self):
        patterns=['*.tmp', 'private-*', '.*']
        converted=json.loads(v3.migrate_options({'PAPERLESS_CONSUMER_IGNORE_PATTERNS': json.dumps(patterns)})['PAPERLESS_CONSUMER_IGNORE_PATTERNS'])
        for filename in ['a.tmp', 'invoice.pdf', 'private-file.pdf', '.hidden']:
            self.assertEqual(any(fnmatch.fnmatchcase(filename,p) for p in patterns), any(re.fullmatch(p,filename) for p in converted))

    def test_new_database_options_win_and_deprecated_options_are_removed(self):
        result=v3.migrate_options({'PAPERLESS_DB_OPTIONS':'sslmode=require', 'PAPERLESS_DBSSLMODE':'prefer', 'PAPERLESS_DB_TIMEOUT':'12', 'PAPERLESS_DB_POOLSIZE':'4'})
        self.assertEqual(result['PAPERLESS_DB_OPTIONS'], 'connect_timeout=12,pool.max_size=4,sslmode=require')
        self.assertFalse(set(v3.DB_OPTIONS) & set(result))

    def test_invalid_database_or_archive_configuration_blocks_before_migration(self):
        for options in [{'PAPERLESS_DBENGINE':'mysql'}, {'PAPERLESS_OCR_MODE':'unknown'}, {'PAPERLESS_ARCHIVE_FILE_GENERATION':'unknown'}, {'PAPERLESS_DBSSLROOTCERT':'invalid,path'}]:
            with self.assertRaises(RuntimeError): v3.migrate_options(options)

    def test_each_x86_cpu_must_meet_the_required_baseline(self):
        supported='flags : pni ssse3 sse4_1 sse4_2 popcnt cx16 lahf_lm\n'
        v3.check_cpu('x86_64',supported)
        v3.check_cpu('aarch64','')
        with self.assertRaisesRegex(RuntimeError,'x86-64-v2'):
            v3.check_cpu('x86_64',supported+'flags : pni ssse3\n')

    def test_custom_scripts_patterns_and_ambiguous_searches_require_review(self):
        options={'PAPERLESS_POST_CONSUME_SCRIPT':'/scripts/after', 'PAPERLESS_CONSUMER_IGNORE_PATTERNS':'["*.tmp"]'}
        categories=v3.review_requirements(options,['preservation'])
        self.assertEqual(categories,['consume_scripts','ignore_patterns','saved_searches'])
        with self.assertRaisesRegex(RuntimeError,'review v3 compatibility'):
            v3.verify_review(options,['preservation'],{})
        review={'fingerprint':v3.review_fingerprint(options,['preservation']), 'acknowledged':categories}
        v3.verify_review(options,['preservation'],review)
        options['PAPERLESS_POST_CONSUME_SCRIPT']='/scripts/changed'
        with self.assertRaises(RuntimeError): v3.verify_review(options,['preservation'],review)

    def test_explicit_oidc_authentication_method_avoids_an_ambiguous_default(self):
        old={'PAPERLESS_SOCIALACCOUNT_PROVIDERS':json.dumps({'openid_connect':{'APPS':[{'settings':{'server_url':'https://login.example.org'}}]}})}
        self.assertIn('oidc',v3.review_requirements(old,[]))
        new=json.loads(old['PAPERLESS_SOCIALACCOUNT_PROVIDERS']);new['openid_connect']['APPS'][0]['settings']['token_auth_method']='client_secret_basic'
        self.assertNotIn('oidc',v3.review_requirements({'PAPERLESS_SOCIALACCOUNT_PROVIDERS':json.dumps(new)},[]))

    def test_explicit_saved_search_fields_do_not_require_unqualified_query_review(self):
        self.assertEqual(v3.review_requirements({},['note:preservation','custom_field:"NS8 proof"']),[])

    def test_shared_view_visibility_change_requires_explicit_review(self):
        shared=[{'id':7,'dashboard':True,'sidebar':True}]
        self.assertIn('shared_saved_views',v3.review_requirements({},[],shared))
        with self.assertRaisesRegex(RuntimeError,'shared_saved_views'):
            v3.verify_review({},[],{},shared)
        review={'fingerprint':v3.review_fingerprint({},[],shared),'acknowledged':['shared_saved_views']}
        v3.verify_review({},[],review,shared)
        with self.assertRaises(RuntimeError):v3.verify_review({},[],review,[{'id':8,'dashboard':True,'sidebar':True}])

    def test_reserved_ocr_output_arguments_are_blocked_before_they_are_ignored(self):
        for key in ['sidecar','output_file','input_file_or_options']:
            with self.assertRaisesRegex(RuntimeError,'reserved OCR'):
                v3.migrate_options({'PAPERLESS_OCR_USER_ARGS':json.dumps({key:'/tmp/example'})})
        original={'PAPERLESS_OCR_USER_ARGS':'{"optimize": 0}'}
        self.assertEqual(v3.migrate_options(original)['PAPERLESS_OCR_USER_ARGS'],original['PAPERLESS_OCR_USER_ARGS'])
