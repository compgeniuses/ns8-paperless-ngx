#!/usr/bin/env python3
"""Exercise real ingestion and original-file downloads through Traefik in QEMU.

Only disposable CI credentials and documents are used. Never run this against
production: the create operation uploads a test document.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import sys
import time

HOST = 'paperless.example.org'
TITLE = 'NS8 upgrade preservation proof'


def request(method, path, body=None, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', 80, timeout=30)
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


def main():
    operation, snapshot_path = sys.argv[1:]
    token = json.loads(request('POST', '/api/token/', json.dumps({
        'username': 'paperlessadmin', 'password': 'Test-only-password-123!'
    }), {'Content-Type': 'application/json'}))['token']
    auth = {'Authorization': f'Token {token}'}
    if operation == 'create':
        boundary = 'NS8PaperlessTestBoundary'
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\n{TITLE}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="upgrade-proof.pdf"\r\n'
                'Content-Type: application/pdf\r\n\r\n').encode() + pdf() + f'\r\n--{boundary}--\r\n'.encode()
        request('POST', '/api/documents/post_document/', body,
                {**auth, 'Content-Type': f'multipart/form-data; boundary={boundary}'})
        deadline = time.monotonic() + 240
        while True:
            documents = json.loads(request('GET', '/api/documents/?title__iexact=NS8%20upgrade%20preservation%20proof', headers=auth))['results']
            if documents:
                break
            if time.monotonic() > deadline:
                raise RuntimeError('Uploaded PDF was not consumed within four minutes')
            time.sleep(5)
        document = documents[0]
    elif operation == 'verify':
        previous = json.loads(Path(snapshot_path).read_text())
        document = json.loads(request('GET', f"/api/documents/{previous['id']}/", headers=auth))
    else:
        raise ValueError('Expected create or verify')
    original = request('GET', f"/api/documents/{document['id']}/download/?original=true", headers=auth)
    assert original == pdf(), 'Original document download changed'
    assert TITLE.lower() in document['content'].lower(), 'Extracted text is missing'
    assert document['title'] == TITLE
    snapshot = {key: document[key] for key in ['id', 'title', 'content', 'created', 'original_file_name']}
    snapshot['sha256'] = hashlib.sha256(original).hexdigest()
    if operation == 'create':
        os.umask(0o077)
        Path(snapshot_path).write_text(json.dumps(snapshot))
    else:
        assert snapshot == previous, 'Document text, dates or metadata changed during module update'
    print('Document ingestion, authentication, text and original download verified')


if __name__ == '__main__':
    main()
