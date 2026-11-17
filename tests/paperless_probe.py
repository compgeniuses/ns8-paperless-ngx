#!/usr/bin/env python3
"""Disposable QEMU-only document ingestion and preservation checks."""
import hashlib
import datetime
import http.client
from http.cookies import SimpleCookie
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import quote, urlencode
import zipfile

HOST = 'paperless.example.org'
TITLE = 'NS8 upgrade preservation proof'


def verify_browser_login():
    cookies = SimpleCookie()
    def exchange(method, path, data=None):
        connection = http.client.HTTPConnection('127.0.0.1', 80, timeout=60)
        headers = {'Host': HOST}
        if cookies:
            headers['Cookie'] = '; '.join(name + '=' + value.value for name, value in cookies.items())
        if data is not None:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        connection.request(method, path, body=data, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        for name, value in response.getheaders():
            if name.lower() == 'set-cookie':
                cookies.load(value)
        status = response.status
        connection.close()
        return status, payload
    class Inputs(HTMLParser):
        def __init__(self):
            super().__init__(); self.values = {}
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'input' and attrs.get('name'):
                self.values[attrs['name']] = attrs.get('value', '')
    status, html = exchange('GET', '/accounts/login/?next=/')
    assert status == 200, f'Browser login form returned HTTP {status}'
    parser = Inputs(); parser.feed(html.decode())
    token = parser.values['csrfmiddlewaretoken']
    username = 'login' if 'login' in parser.values else 'username'
    status, _ = exchange('POST', '/accounts/login/?next=/', urlencode({
        username: 'paperlessadmin', 'password': 'Test-only-password-123!',
        'csrfmiddlewaretoken': token, 'next': '/'}))
    assert status in (302, 303), f'Browser session login returned HTTP {status}'
    status, _ = exchange('GET', '/api/documents/?page_size=1')
    assert status == 200, f'Browser session cookie was not authenticated: HTTP {status}'


def request(method, path, body=None, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', 80, timeout=60)
    connection.request(method, path, body=body, headers={'Host': HOST, **(headers or {})})
    response = connection.getresponse()
    data = response.read()
    connection.close()
    if not 200 <= response.status < 300:
        raise RuntimeError(f'{method} {path} returned HTTP {response.status}')
    return data


def pdf():
    stream = b'BT /F1 18 Tf 72 720 Td (NS8 upgrade preservation proof) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    result = b'%PDF-1.4\n'
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n'
    xref = len(result)
    result += b'xref\n0 6\n0000000000 65535 f \n'
    result += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets)
    result += f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    return result


def fixture(kind, stage):
    title = TITLE if kind == 'pdf' else f'NS8 {stage} {kind.upper()} preservation proof'
    if kind == 'pdf':
        return title, 'application/pdf', pdf()
    if kind == 'docx':
        parts = {
            '[Content_Types].xml': '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
            '_rels/.rels': '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
            'word/document.xml': f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{title}</w:t></w:r></w:p><w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr></w:body></w:document>',
        }
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in parts.items():
                info = zipfile.ZipInfo(name, date_time=(2024, 1, 2, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, value)
        return title, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', output.getvalue()
    if kind == 'eml':
        payload = (f'From: Alice <alice@example.org>\r\nTo: Bob <bob@example.org>\r\n'
                   f'Subject: {title}\r\nDate: Tue, 02 Jan 2024 12:00:00 +0000\r\n'
                   f'Message-ID: <ns8-{stage}-proof@example.org>\r\n'
                   'MIME-Version: 1.0\r\nContent-Type: text/plain; charset=utf-8\r\n'
                   f'Content-Transfer-Encoding: 8bit\r\n\r\n{title}\r\n')
        return title, 'message/rfc822', payload.encode()
    raise ValueError(kind)


def wait_document(title, auth):
    deadline = time.monotonic() + 300
    while True:
        documents = json.loads(request('GET', '/api/documents/?title__iexact=' + quote(title), headers=auth))['results']
        documents = [item for item in documents if item['title'] == title]
        if documents:
            return documents[0]
        if time.monotonic() > deadline:
            raise RuntimeError(f'Document was not consumed: {title}')
        time.sleep(5)


def inspect_document(document, kind, stage, auth):
    title, _, payload = fixture(kind, stage)
    original = request('GET', f"/api/documents/{document['id']}/download/?original=true", headers=auth)
    assert original == payload, f'{kind}: original file changed'
    assert title.lower() in document['content'].lower(), f'{kind}: extracted text missing'
    assert document['title'] == title
    archive = request('GET', f"/api/documents/{document['id']}/download/?original=false", headers=auth)
    assert archive.startswith(b'%PDF-'), f'{kind}: archive is not a PDF'
    deadline = time.monotonic() + 60
    while True:
        results = json.loads(request('GET', '/api/documents/?query=preservation', headers=auth))['results']
        if any(item['id'] == document['id'] for item in results):
            break
        if time.monotonic() > deadline:
            raise RuntimeError(f'{kind}: missing from full-text search')
        time.sleep(3)
    snapshot = {key: document[key] for key in ['id', 'title', 'content', 'created', 'original_file_name']}
    snapshot.update(correspondent=document.get('correspondent'),
                    document_type=document.get('document_type'),
                    tags=sorted(document.get('tags', [])),
                    custom_fields=sorted(({'field': value['field'], 'value': value['value']}
                                          for value in document.get('custom_fields', [])),
                                         key=lambda value: value['field']))
    notes = json.loads(request('GET', f"/api/documents/{document['id']}/notes/", headers=auth))
    snapshot['notes'] = sorted(({'note':note['note'],'format':note.get('format','plain')} for note in notes),key=lambda note:note['note'])
    snapshot.update(kind=kind, stage=stage, sha256=hashlib.sha256(original).hexdigest(), archive_sha256=hashlib.sha256(archive).hexdigest())
    return snapshot


def seed_metadata(document, auth):
    def create(endpoint, payload):
        return json.loads(request('POST', '/api/' + endpoint + '/', json.dumps(payload),
                                  {**auth, 'Content-Type': 'application/json'}))
    tag = create('tags', {'name': 'NS8 preservation tag', 'color': '#00aaff'})
    correspondent = create('correspondents', {'name': 'NS8 preservation correspondent'})
    document_type = create('document_types', {'name': 'NS8 preservation document type'})
    custom = create('custom_fields', {'name': 'NS8 preservation field', 'data_type': 'string'})
    user=json.loads(request('GET','/api/users/?username__iexact=paperlessadmin',headers=auth))['results'][0]
    view = create('saved_views', {'name': 'NS8 preservation saved view', 'owner':user['id'],
                  'show_on_dashboard': True, 'show_in_sidebar': True,
                  'filter_rules': [{'rule_type': 20, 'value': 'note:preservation'}]})
    if 'show_on_dashboard' not in view:
        request('PATCH',f"/api/saved_views/{view['id']}/",json.dumps({'show_on_dashboard':True,'show_in_sidebar':True}),{**auth,'Content-Type':'application/json','Accept':'application/json; version=9'})
    payload = {'tags': [tag['id']], 'correspondent': correspondent['id'],
               'document_type': document_type['id'],
               'custom_fields': [{'field': custom['id'], 'value': 'NS8 custom value proof'}]}
    document = json.loads(request('PATCH', f"/api/documents/{document['id']}/", json.dumps(payload),
                                  {**auth, 'Content-Type': 'application/json'}))
    request('POST', f"/api/documents/{document['id']}/notes/", json.dumps({'note': 'NS8 note preservation proof **literal markers**', 'format':'plain'}),
            {**auth, 'Content-Type': 'application/json'})
    resources = [{'endpoint': endpoint, 'id': value['id'], 'name': value['name']}
                 for endpoint, value in [('tags', tag), ('correspondents', correspondent),
                                          ('document_types', document_type), ('custom_fields', custom)]]
    metadata = {'resources': resources, 'document_id': document['id'],
                'token_sha256':hashlib.sha256(auth['Authorization'].encode()).hexdigest(),
                'saved_view': {'id': view['id'], 'name': view['name'], 'owner':user['id']}}
    if 'parent' in tag:
        parent=create('tags',{'name':'NS8 hierarchy parent'})
        child=create('tags',{'name':'NS8 hierarchy child','parent':parent['id']})
        assert child['parent']==parent['id']
        metadata['tag_hierarchy']={'parent':parent['id'],'child':child['id']}
    return document, metadata


def verify_metadata(snapshot, auth):
    assert hashlib.sha256(auth['Authorization'].encode()).hexdigest()==snapshot['token_sha256'], 'Original API token changed'
    for resource in snapshot['resources']:
        actual = json.loads(request('GET', f"/api/{resource['endpoint']}/{resource['id']}/", headers=auth))
        assert actual['name'] == resource['name'], resource
    if snapshot.get('tag_hierarchy'):
        hierarchy=snapshot['tag_hierarchy']
        child=json.loads(request('GET',f"/api/tags/{hierarchy['child']}/",headers=auth))
        assert child['parent']==hierarchy['parent'],'Tag hierarchy changed'
    view = json.loads(request('GET', f"/api/saved_views/{snapshot['saved_view']['id']}/", headers=auth))
    if 'show_on_dashboard' not in view:
        view=json.loads(request('GET',f"/api/saved_views/{snapshot['saved_view']['id']}/",headers={**auth,'Accept':'application/json; version=9'}))
    assert view['name'] == snapshot['saved_view']['name']
    assert view['owner'] == snapshot['saved_view']['owner']
    assert view['show_on_dashboard'] is True and view['show_in_sidebar'] is True
    assert len(view['filter_rules']) == 1 and view['filter_rules'][0]['rule_type'] == 20
    # v3's explicit note-field rewrite is an upstream data migration.
    assert view['filter_rules'][0]['value'] in ('note:preservation', 'notes.note:preservation')
    deadline = time.monotonic() + 120
    while True:
        results = json.loads(request('GET', '/api/documents/?query=' + quote(view['filter_rules'][0]['value']), headers=auth))['results']
        if any(item['id'] == snapshot['document_id'] for item in results):
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('Saved-view note search no longer finds the preserved document')
        time.sleep(3)


def main():
    operation, snapshot_path = sys.argv[1:]
    verify_browser_login()
    token = json.loads(request('POST', '/api/token/', json.dumps({
        'username': 'paperlessadmin', 'password': 'Test-only-password-123!'
    }), {'Content-Type': 'application/json'}))['token']
    auth = {'Authorization': f'Token {token}'}
    if operation in ('create', 'create-after'):
        stage = 'before' if operation == 'create' else 'after'
        kinds = ['pdf', 'docx', 'eml'] if stage == 'before' else ['docx', 'eml']
        snapshots = []
        metadata = None
        for kind in kinds:
            title, mime, payload = fixture(kind, stage)
            boundary = 'NS8PaperlessTestBoundary'
            body = (f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\n{title}\r\n'
                    f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="upgrade-proof-{stage}.{kind}"\r\n'
                    f'Content-Type: {mime}\r\n\r\n').encode() + payload + f'\r\n--{boundary}--\r\n'.encode()
            request('POST', '/api/documents/post_document/', body,
                    {**auth, 'Content-Type': f'multipart/form-data; boundary={boundary}'})
            document = wait_document(title, auth)
            if kind == 'pdf' and stage == 'before':
                document, metadata = seed_metadata(document, auth)
            snapshots.append(inspect_document(document, kind, stage, auth))
        os.umask(0o077)
        Path(snapshot_path).write_text(json.dumps(snapshots))
        if metadata:
            Path(snapshot_path + '.metadata.json').write_text(json.dumps(metadata))
    elif operation == 'verify':
        for previous in json.loads(Path(snapshot_path).read_text()):
            document = json.loads(request('GET', f"/api/documents/{previous['id']}/", headers=auth))
            actual = inspect_document(document, previous['kind'], previous['stage'], auth)
            # Upstream 2.17 intentionally changes created timestamps to dates.
            # Fixtures use UTC; the module separately archives exact timestamps.
            if len(actual['created']) == 10 and len(previous['created']) > 10:
                previous['created'] = datetime.datetime.fromisoformat(previous['created'].replace('Z', '+00:00')).astimezone(datetime.timezone.utc).date().isoformat()
            assert actual == previous, f"{previous['kind']}: document metadata, text or archive changed"
        metadata_path = Path(snapshot_path + '.metadata.json')
        if metadata_path.exists():
            verify_metadata(json.loads(metadata_path.read_text()), auth)
    else:
        raise ValueError('Expected create, create-after or verify')
    print('PDF/Office/email ingestion, original/archive bytes, metadata, login and search verified')


if __name__ == '__main__':
    main()
