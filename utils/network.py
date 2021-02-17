import ssl
import urllib
import shutil
import json
import os
from urllib.parse import urlparse


def ssl_context():
    if os.environ.get('STAC_DEBUG', False):
        return ssl._create_unverified_context()
    return ssl.SSLContext()


def request(api, url, data=None, headers=None):
    url, headers, data = api.auth.authenticate(url, headers, data)

    if data is not None:
        body_bytes = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, body_bytes)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Content-Length', len(body_bytes))
    else:
        req = urllib.request.Request(url)

    if headers is not None:
        for key, value in headers.items():
            req.add_header(key, value)

    r = urllib.request.urlopen(req, context=ssl_context(), timeout=5)
    response = r.read()

    return json.loads(response)


def download(url, path):
    parsed_url = urlparse(url)

    if parsed_url.scheme in ['http', 'https']:
        with urllib.request.urlopen(
                url,
                context=ssl_context(),
                timeout=5) as response, \
                open(path, 'wb') as f:
            shutil.copyfileobj(response, f)
