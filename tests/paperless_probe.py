#!/usr/bin/env python3
"""Disposable QEMU-only document ingestion and preservation checks."""
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import quote
import zipfile

HOST = 'paperless.example.org'
TITLE = 'NS8 upgrade preservation proof'


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
    snapshot.update(kind=kind, stage=stage, sha256=hashlib.sha256(original).hexdigest(), archive_sha256=hashlib.sha256(archive).hexdigest())
    return snapshot


def main():
    operation, snapshot_path = sys.argv[1:]
    token = json.loads(request('POST', '/api/token/', json.dumps({
        'username': 'paperlessadmin', 'password': 'Test-only-password-123!'
    }), {'Content-Type': 'application/json'}))['token']
    auth = {'Authorization': f'Token {token}'}
    if operation in ('create', 'create-after'):
        stage = 'before' if operation == 'create' else 'after'
        kinds = ['pdf', 'docx', 'eml'] if stage == 'before' else ['docx', 'eml']
        snapshots = []
        for kind in kinds:
            title, mime, payload = fixture(kind, stage)
            boundary = 'NS8PaperlessTestBoundary'
            body = (f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\n{title}\r\n'
                    f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="upgrade-proof-{stage}.{kind}"\r\n'
                    f'Content-Type: {mime}\r\n\r\n').encode() + payload + f'\r\n--{boundary}--\r\n'.encode()
            request('POST', '/api/documents/post_document/', body,
                    {**auth, 'Content-Type': f'multipart/form-data; boundary={boundary}'})
            snapshots.append(inspect_document(wait_document(title, auth), kind, stage, auth))
        os.umask(0o077)
        Path(snapshot_path).write_text(json.dumps(snapshots))
    elif operation == 'verify':
        for previous in json.loads(Path(snapshot_path).read_text()):
            document = json.loads(request('GET', f"/api/documents/{previous['id']}/", headers=auth))
            actual = inspect_document(document, previous['kind'], previous['stage'], auth)
            assert actual == previous, f"{previous['kind']}: document metadata, text or archive changed"
    else:
        raise ValueError('Expected create, create-after or verify')
    print('PDF/Office/email ingestion, original/archive bytes, metadata, login and search verified')


if __name__ == '__main__':
    main()
