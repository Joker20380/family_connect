"""Disposable local subscription HTTPS stand; never opens an existing product DB."""
import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import ipaddress
import json
from pathlib import Path
import ssl
import time
import zipfile

from control.friends.access import Access
from control.friends import paid_beta, support_ids


ROOT = Path(__file__).resolve().parents[1]


def prepare(work):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    private = work / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    assert not (private / 'synthetic.sqlite').exists()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, 'Disposable subscription qualification')])
    now = datetime.now(timezone.utc)
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=5))
          .not_valid_after(now + timedelta(days=2)).add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
          .sign(key, hashes.SHA256()))
    leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    leaf = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, '10.0.2.2')]))
            .issuer_name(name).public_key(leaf_key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('10.0.2.2')),
                                                      x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
            .sign(key, hashes.SHA256()))
    (private / 'ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (private / 'server.pem').write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
    (private / 'server.key').write_bytes(leaf_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    (private / 'server.key').chmod(0o600)
    access = Access(private / 'synthetic.sqlite')
    access.initialize()
    with access.db() as database:
        paid_beta.migrate(database)
    (private / 'invitation').write_text(access.invite())
    (private / 'mode').write_text('normal')
    with zipfile.ZipFile(work / 'inputs/base118.apk') as archive:
        for name in archive.namelist():
            if name.startswith('lib/x86_64/') and name.endswith('.so') and 'chaquopy' not in name and 'python' not in name:
                target = work / 'native/jniLibs/x86_64' / Path(name).name
            elif name.startswith(('assets/awg-', 'assets/restricted-', 'assets/audio-')):
                target = work / 'native' / name
            else:
                continue
            if name.endswith('/'):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))


def scenario(work, action):
    private = work / 'private'
    assert (private / 'synthetic.sqlite').is_file()
    if action in ('normal', 'unsupported', 'unavailable', 'slow'):
        (private / 'mode').write_text(action)
        return
    access = Access(private / 'synthetic.sqlite')
    now = int(time.time())
    with access.db() as database:
        devices = database.execute('SELECT device FROM devices').fetchall()
        assert len(devices) == 1, 'Exactly one disposable identity required'
        device = devices[0]['device']
        if action == 'identity-revoked':
            database.execute('UPDATE devices SET revoked=1 WHERE device=?', (device,))
            return
        support = support_ids.registered(database, device)
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=?,last_seen=? WHERE device=?',
                         ('android', paid_beta.PAID_ANDROID_VERSION, paid_beta.PAID_ANDROID_VERSION_CODE, now, device))
        previous = database.execute('SELECT paid_until,grace_until,version FROM paid_beta_subscriptions WHERE device=?', (device,)).fetchone()
        number = previous['version'] + 1 if previous else 1
        kind = 'payment' if action in ('active', 'snapshot-only') else action
        values = {}
        if kind == 'payment':
            values = dict(period_start=now, paid_until=max(now, previous['paid_until'] if previous else 0,
                          previous['grace_until'] or 0 if previous else 0) + 3600, apk_sha256=paid_beta.PAID_ANDROID_APK_SHA256)
        elif kind == 'grace':
            values = dict(grace_until=max(now, previous['paid_until'], previous['grace_until'] or 0) + 3600)
        event_id = f'synthetic-android-event-{number}'
        paid_beta.apply_event(database, support, kind, event_id, 'SYNTHETIC-ONLY-NO-PAYMENT', now=now, **values)
        if action == 'snapshot-only':
            database.execute('UPDATE paid_beta_subscriptions SET last_event_id=? WHERE device=?',
                             (f'synthetic-unavailable-event-{number}', device))


def serve(work):
    spec = importlib.util.spec_from_file_location('subscription_android_handler', ROOT / 'deploy/friends/access-api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = work / 'private'
    module.access = Access(module.ROOT / 'synthetic.sqlite')
    class Handler(module.Handler):
        def do_POST(self):
            mode = (work / 'private/mode').read_text()
            if self.path == '/friends/device/subscription' and mode in ('unsupported', 'unavailable'):
                self.reply(404 if mode == 'unsupported' else 503, dict(error=mode))
                return
            super().do_POST()

        def reply(self, status, value):
            if self.path == '/friends/device/subscription' and (work / 'private/mode').read_text() == 'slow':
                time.sleep(2)
            with (work / 'logs/http.jsonl').open('a') as output:
                output.write(json.dumps(dict(path=self.path, status=status, at=int(time.time()))) + '\n')
            super().reply(status, value)

    server = module.ThreadingHTTPServer(('127.0.0.1', 18443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(work / 'private/server.pem', work / 'private/server.key')
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print('Disposable HTTPS handler ready on loopback:18443', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'serve', 'scenario'))
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--action', choices=('normal', 'unsupported', 'unavailable', 'slow', 'active', 'snapshot-only', 'grace', 'expire', 'revoke', 'identity-revoked'))
    arguments = parser.parse_args()
    work = arguments.work.resolve()
    assert work.name in ('subscription-android-1', 'subscription-android-2') and (work / 'private').is_dir()
    if arguments.operation == 'scenario':
        assert arguments.action
        scenario(work, arguments.action)
    else:
        globals()[arguments.operation](work)
