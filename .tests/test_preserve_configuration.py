import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class Configuration(unittest.TestCase):
    def test_partial_configuration_preserves_password_and_extra_options(self):
        stored={'PAPERLESS_ADMIN_PASSWORD':'existing-secret','PAPERLESS_TIME_ZONE':'UTC','PAPERLESS_NGX_NAME':'Existing name','PAPERLESS_OCR_MODE':'force'}
        writes={}
        agent=types.SimpleNamespace(set_progress=lambda value:None,redis_connect=lambda **kw:None,get_smarthost_settings=lambda r:{'host':'','port':25,'username':'','password':'','tls_verify':False},read_envfile=lambda f:stored,write_envfile=lambda f,v:writes.update({f:v}),dump_env=lambda:None,unset_env=lambda k:None)
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'paperless-ngx.env';target.touch()
            old=Path.cwd();os.chdir(td)
            try:
                with patch.dict('sys.modules',agent=agent),patch('sys.stdin',io.StringIO('{"host":"paperless.example.org","PAPERLESS_ADMIN_PASSWORD":""}')):
                    runpy.run_path(str(ROOT/'imageroot/actions/configure-module/20configure'),run_name='__main__')
            finally:os.chdir(old)
        result=writes['paperless-ngx.env']
        for key in ['PAPERLESS_ADMIN_PASSWORD','PAPERLESS_TIME_ZONE','PAPERLESS_NGX_NAME','PAPERLESS_OCR_MODE']:self.assertEqual(result[key],stored[key])

    def test_read_configuration_never_returns_password(self):
        secret='must-not-be-returned'
        agent=types.SimpleNamespace(read_envfile=lambda f:{'PAPERLESS_ADMIN_PASSWORD':secret,'PAPERLESS_TIME_ZONE':'UTC'})
        output=io.StringIO()
        with patch.dict('sys.modules',agent=agent),patch('os.path.exists',return_value=True),contextlib.redirect_stdout(output):
            runpy.run_path(str(ROOT/'imageroot/actions/get-configuration/20read'),run_name='__main__')
        result=json.loads(output.getvalue());self.assertEqual(result['PAPERLESS_ADMIN_PASSWORD'],'');self.assertEqual(result['PAPERLESS_TIME_ZONE'],'UTC');self.assertNotIn(secret,output.getvalue())

if __name__=='__main__':unittest.main()
