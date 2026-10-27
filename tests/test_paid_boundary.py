import io
import json
from pathlib import Path
import sqlite3
import subprocess
import tarfile
import time
import zipfile

from cryptography import x509
import pytest

from control.friends import paid_beta
from control.friends.restricted_admin import publish_crl
from scripts.package_paid_boundary import build, digest, source_gate
from test_friends_http_runtime import request, running, runtime


def write_zip(path, files):
    with zipfile.ZipFile(path, 'w') as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)


def test_committed_bundle_deterministic_closed_and_inventoried(tmp_path):
    first, second = tmp_path / 'first.tar', tmp_path / 'second.tar'
    report = build(first)
    assert report == build(second)
    assert first.read_bytes() == second.read_bytes()
    with tarfile.open(first) as archive:
        names = archive.getnames()
        assert len(names) == report['member_count'] == len(set(names))
        assert not any(name.endswith(('.db', '.key', '.pem', '.env', '.conf')) for name in names)
        inventory = json.load(archive.extractfile('inventory.json'))
        for name, expected in inventory['files'].items():
            raw = archive.extractfile(name).read()
            assert expected == dict(size=len(raw), sha256=digest(raw))
        with zipfile.ZipFile(io.BytesIO(archive.extractfile('artifacts/friends-http.pyz').read())) as runtime_archive:
            raw = runtime_archive.read('control/friends/paid_beta.py')
            assert raw == subprocess.check_output(['git', 'show', report['source_commit'] + ':control/friends/paid_beta.py'])
        assert 'source/control_plane/apps/console/collector.py' in names
        assert 'artifacts/paid-beta.pyz' in names
        assert 'artifacts/restricted-sync.pyz' in names


@pytest.mark.parametrize('change', ['removed', 'modified', 'added', 'paid_removed'])
def test_source_gate_blocks_unrelated_drift(tmp_path, change):
    served, candidate = tmp_path / 'served.pyz', tmp_path / 'candidate.pyz'
    before = {'other.py': b'preserve', 'control/friends/restricted.py': b'legacy'}
    after = dict(before, **{'control/friends/restricted.py': b'paid', 'control/friends/paid_beta.py': b'authority'})
    if change == 'removed':
        del after['other.py']
    elif change == 'modified':
        after['other.py'] = b'changed'
    elif change == 'added':
        after['new.py'] = b'unreviewed'
    else:
        del after['control/friends/paid_beta.py']
    write_zip(served, before)
    write_zip(candidate, after)
    assert source_gate(served, candidate)['result'] == 'BLOCKED_SERVED_SOURCE_DRIFT'


def test_source_gate_accepts_only_paid_delta(tmp_path):
    served, candidate = tmp_path / 'served.pyz', tmp_path / 'candidate.pyz'
    write_zip(served, {'control/friends/restricted.py': b'legacy', 'same.py': b'same'})
    write_zip(candidate, {'control/friends/restricted.py': b'paid', 'same.py': b'same', 'control/friends/paid_beta.py': b'authority'})
    assert source_gate(served, candidate)['result'] == 'PASS'


def test_synthetic_backup_restore_expiry_and_restart(runtime, tmp_path):
    access, device = runtime['access'], runtime['canary']
    now = int(time.time())
    with access.db() as database:
        database.execute('UPDATE device_support SET platform=?,app_version=?,version_code=106,last_seen=? WHERE device=?',
            ('android', paid_beta.VERSION, now, device.reference))
        support = database.execute('SELECT support_id FROM device_support WHERE device=?', (device.reference,)).fetchone()[0]
    (runtime['state'] / 'admission.json').write_text('{"version":2,"eligibility":"all_activated"}')
    expires = now + 8
    with paid_beta.connection(access.path, write=True) as database:
        paid_beta.apply_event(database, support, 'payment', 'synthetic-recovery-001', 'synthetic-reference', now=now,
            period_start=now, paid_until=expires, apk_sha256=paid_beta.APK_SHA256)
    backup = tmp_path / 'synthetic-backup.db'
    with sqlite3.connect(access.path.resolve().as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    restored = tmp_path / 'synthetic-restored.db'
    with sqlite3.connect(backup) as source, sqlite3.connect(restored) as target:
        source.backup(target)
        assert target.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        assert target.execute('PRAGMA foreign_key_check').fetchall() == []
    with paid_beta.connection(restored, write=True) as database:
        paid_beta.migrate(database)
        paid_beta.migrate(database)
        assert paid_beta.effective_subscription_state(database, device.reference, now).allowed
        assert not paid_beta.effective_subscription_state(database, device.reference, expires).allowed
        assert database.execute('SELECT count(*) FROM paid_beta_events').fetchone()[0] == 1
    identity = runtime['identities']['canary']
    with running(runtime):
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)
        assert status == 200
        proof = device.prove_transport_key(json.loads(raw)['challenge'])
        status, raw = request(runtime['backend'], '/friends/restricted-readiness', body=proof)
        assert status == 200
        delivery = json.loads(raw)
        certificate = x509.load_pem_x509_certificate(delivery['certificate'].encode())
        assert delivery['expires_at'] == certificate.not_valid_after_utc.timestamp() == expires
        status, raw = request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)
        assert status == 200
        pending = device.prove_transport_key(json.loads(raw)['challenge'])
        time.sleep(max(0, expires - time.time()) + .1)
        assert request(runtime['backend'], '/friends/restricted-readiness', body=pending)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness', body=proof)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)[0] == 403
    runtime['restricted'].access.clock = lambda: expires
    crl_path = tmp_path / 'synthetic-crl.pem'
    publish_crl(runtime['restricted'], crl_path)
    crl = x509.load_pem_x509_crl(crl_path.read_bytes())
    assert crl.get_revoked_certificate_by_serial_number(certificate.serial_number) is None
    assert certificate.not_valid_after_utc.timestamp() <= time.time()
    with running(runtime):
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=identity)[0] == 403
        assert request(runtime['backend'], '/friends/restricted-readiness/challenge', body=runtime['identities']['non_canary'][0])[0] == 200
