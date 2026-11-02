"""Read-only HTTPS acceptance of both invitation routes and the Windows mirror."""
import base64
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://185.251.89.19:8443'
CATALOG = 'https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/windows.json'


def policy(html):
    text = html.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    digests = {}
    for tag in ('script', 'style'):
        matches = re.findall('<' + tag + '>(.*?)</' + tag + '>', text, re.S)
        if len(matches) != 1:
            raise ValueError('Expected one inline ' + tag)
        digests[tag] = base64.b64encode(hashlib.sha256(matches[0].encode()).digest()).decode()
    return ("default-src 'none'; script-src 'sha256-" + digests['script'] +
            "'; style-src 'sha256-" + digests['style'] +
            "'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")


def verify_page(actual, header, expected):
    if actual != expected:
        raise ValueError('Public invitation differs from reviewed source')
    if header != policy(actual):
        raise ValueError('Public invitation CSP does not bind its inline script/style')


def verify_catalog(raw, expected, public_key, now):
    if raw != expected:
        raise ValueError('Public Windows catalog differs from signed source')
    envelope = json.loads(raw)
    payload = base64.b64decode(envelope['payload'], validate=True)
    Ed25519PublicKey.from_public_bytes(public_key).verify(
        base64.b64decode(envelope['signature'], validate=True), b'family-connect/app-update/v2\0' + payload)
    data = json.loads(payload)
    if (data['schema'] != 2 or data['platform'] != 'windows' or data['sequence'] < 1 or
            not data['issued_at'] <= now < data['expires_at'] <= data['issued_at'] + 90 * 86400 or
            not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', data['version'])):
        raise ValueError('Invalid Windows catalog identity/lease')
    name = 'FamilyConnect-Setup-' + data['version'] + '-pilot-unsigned.exe'
    url = 'https://github.com/Joker20380/family_connect/releases/download/windows-v' + data['version'] + '/' + name
    if (data['artifact']['url'] != url or not 1 <= data['artifact']['size'] <= 512 * 1024 * 1024 or
            not re.fullmatch('[0-9a-f]{64}', data['artifact']['sha256'])):
        raise ValueError('Invalid Windows artifact binding')
    return data, name


def verify_stream(stream, expected):
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024 * 1024):
        size += len(chunk)
        if size > expected['size']:
            raise ValueError('Public artifact exceeds signed size')
        digest.update(chunk)
    if size != expected['size'] or digest.hexdigest() != expected['sha256']:
        raise ValueError('Public artifact differs from signed hash/size')
    return dict(size=size, sha256=digest.hexdigest())


def main():
    expected = (ROOT / 'deploy/friends/invite/index.html').read_bytes()
    for route in ('/i/', '/invite/'):
        with urllib.request.urlopen(BASE + route, timeout=30) as response:
            verify_page(response.read(128 * 1024), response.headers.get('Content-Security-Policy'), expected)
    with urllib.request.urlopen(CATALOG, timeout=30) as response:
        data, name = verify_catalog(response.read(65537), (ROOT / 'updates/windows.json').read_bytes(),
                                   base64.b64decode((ROOT / 'clients/windows/update.pub').read_bytes().strip()), int(time.time()))
    if ('/downloads/' + name).encode() not in expected:
        raise ValueError('Invitation does not advertise current signed Windows version')
    with urllib.request.urlopen(BASE + '/downloads/' + name, timeout=120) as response:
        artifact = verify_stream(response, data['artifact'])
    print(json.dumps(dict(result='PASS', routes=['/i/', '/invite/'], csp='PASS',
                         windows_version=data['version'], sequence=data['sequence'], artifact=artifact), sort_keys=True))


if __name__ == '__main__':
    main()
