"""Read-only HTTPS acceptance of invitations and signed Windows/Android downloads."""
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


def verify_android_catalog(raw, expected, legacy_raw, public_key, now):
    if len(raw) > 16384 or len(legacy_raw) > 8192 or raw != expected:
        raise ValueError('Public Android catalog differs from signed source or exceeds bounds')
    envelope = json.loads(raw)
    payload = base64.b64decode(envelope['payload'], validate=True)
    Ed25519PublicKey.from_public_bytes(public_key).verify(
        base64.b64decode(envelope['signature'], validate=True), b'family-connect/android-update/v1\0' + payload)
    data = json.loads(payload)
    integers = ('schema', 'sequence', 'version_code', 'size', 'issued_at', 'expires_at',
                'minimum_supported_version', 'mandatory_after')
    if any(type(data.get(field)) is not int for field in integers):
        raise ValueError('Invalid Android integer field')
    if (data['schema'] != 1 or data['channel'] != 'android-field' or
            data['package'] != 'com.familyconnect.app.friends' or data['abi'] != 'arm64-v8a' or
            data['signer_fingerprint'] != '67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a' or
            not 1 <= data['sequence'] < 10**15 or not 1 <= data['version_code'] <= 2147483647 or
            not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-beta' + str(data['version_code']), data['version'])):
        raise ValueError('Invalid Android identity')
    if (not data['issued_at'] <= now < data['expires_at'] <= data['issued_at'] + 90 * 86400 or
            not 1 <= data['minimum_supported_version'] <= data['version_code'] or
            data['mandatory_after'] != 0 and not data['issued_at'] <= data['mandatory_after'] < data['expires_at']):
        raise ValueError('Invalid Android lease/policy')
    name = 'FamilyConnect-Test-' + data['version'] + '.apk'
    if (data['url'] != BASE + '/downloads/' + name or not 1024 <= data['size'] <= 150_000_000 or
            not re.fullmatch('[0-9a-f]{64}', data['sha256'])):
        raise ValueError('Invalid Android artifact binding')
    fields = ('schema', 'package', 'abi', 'version_code', 'version', 'url', 'size', 'sha256')
    if json.loads(legacy_raw) != {field: data[field] for field in fields}:
        raise ValueError('Legacy Android discovery differs from signed catalog')
    return data, name


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
    with urllib.request.urlopen(BASE + '/updates/android-friends-v2.json', timeout=30) as response:
        android_raw = response.read(16385)
    with urllib.request.urlopen(BASE + '/updates/android-friends.json', timeout=30) as response:
        legacy_raw = response.read(8193)
    android, android_name = verify_android_catalog(
        android_raw, (ROOT / 'updates/android-friends-v2.json').read_bytes(), legacy_raw,
        base64.b64decode((ROOT / 'clients/desktop/update.pub').read_bytes().strip()), int(time.time()))
    if ('/downloads/' + android_name).encode() not in expected:
        raise ValueError('Invitation does not advertise current signed Android version')
    with urllib.request.urlopen(BASE + '/downloads/' + android_name, timeout=120) as response:
        android_artifact = verify_stream(response, android)
    print(json.dumps(dict(result='PASS', routes=['/i/', '/invite/'], csp='PASS',
                         windows_version=data['version'], sequence=data['sequence'], artifact=artifact,
                         android_version=android['version'], android_sequence=android['sequence'],
                         android_artifact=android_artifact), sort_keys=True))


if __name__ == '__main__':
    main()
