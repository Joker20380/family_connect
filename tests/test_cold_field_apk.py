import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
import zipfile

import pytest

from scripts.prepare_cold_field_apk import check_window, compare_payload, entries, prepare
from scripts import prepare_cold_field_apk as finalizer


def test_window_keeps_candidate_and_handoff_budgets():
    locator = dict(locator_sha256='a'*64, expires_at=1500)
    ready = dict(phase='LOCATOR_VERIFIED_SEED_CONNECTED', locator_sha256='a'*64, expires_at=1500, observed_at=1200)
    check_window(locator, ready, now=1201, handoff_seconds=60)
    for change in ({'observed_at': 1000}, {'locator_sha256': 'b'*64}, {'expires_at': 1501}, {'phase': 'STOPPED'}):
        with pytest.raises(ValueError):
            check_window(locator, dict(ready, **change), now=1201, handoff_seconds=60)
    with pytest.raises(ValueError):
        check_window(locator, ready, now=1241, handoff_seconds=60)


def test_final_verification_rejects_altered_prepared_payload():
    prebuild = {'classes.dex': b'accepted', 'lib/arm64-v8a/libfc_restricted.so': b'native'}
    fresh = dict(prebuild, **{'assets/provisioning/nl-amsterdam-1.json': b'locator'})
    finalizer.compare_fresh_payload(prebuild, fresh, 'nl-amsterdam-1')
    for changed in (dict(fresh, **{'classes.dex': b'changed'}), dict(fresh, **{'assets/extra': b'extra'})):
        with pytest.raises(ValueError):
            finalizer.compare_fresh_payload(prebuild, changed, 'nl-amsterdam-1')


def test_same_version_receipt_cannot_replace_qualified_prebuild(tmp_path, monkeypatch):
    receipt = tmp_path/'verification.json'
    receipt.write_text(json.dumps(dict(unsigned=True, package=finalizer.PACKAGE, version_code=120,
                                       source_commit='a'*40, apk_sha256='b'*64)))
    accepted = dict(head_sha='c'*40, verification_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest())
    monkeypatch.setattr(finalizer, 'qualification', lambda: accepted)
    with pytest.raises(ValueError, match='CI source mismatch'):
        finalizer.accepted_prebuild(SimpleNamespace(verification=receipt))
    receipt.write_text(receipt.read_text()+'\n')
    with pytest.raises(ValueError, match='unqualified CI receipt'):
        finalizer.accepted_prebuild(SimpleNamespace(verification=receipt))


def test_signature_does_not_hide_changed_payload(tmp_path):
    source, signed = tmp_path/'source.apk', tmp_path/'signed.apk'
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr('classes.dex', b'accepted')
        archive.writestr('assets/provisioning/nl-amsterdam-1.json', b'locator')
    for replacement in (False, True):
        with zipfile.ZipFile(signed, 'w') as archive:
            for name, raw in entries(source).items():
                archive.writestr(name, b'changed' if replacement and name == 'classes.dex' else raw)
            archive.writestr('META-INF/SIGNER.SF', b'signature')
        if replacement:
            with pytest.raises(ValueError):
                compare_payload(source, signed)
        else:
            compare_payload(source, signed)


def test_duplicate_zip_entries_rejected(tmp_path):
    apk = tmp_path/'duplicate.apk'
    with zipfile.ZipFile(apk, 'w') as archive:
        archive.writestr('classes.dex', b'one')
        with pytest.warns(UserWarning):
            archive.writestr('classes.dex', b'two')
    with pytest.raises(ValueError):
        entries(apk)


def test_real_zipalign_fresh_asset_packaging_offline(tmp_path, monkeypatch):
    prebuild, package, zipalign = (os.environ.get(name) for name in ('FC_FIELD_PREBUILD', 'FC_ENTRY_PACKAGE', 'FC_ZIPALIGN'))
    if not all((prebuild, package, zipalign)):
        pytest.skip('requires accepted unsigned APK, packaged verifier, real SDK zipalign')
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('offline_only_authority', root/'tests/fixtures/mobile_bootstrap/provision_backend.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    authority = tmp_path/'SYNTHETIC_NOT_FOR_DELIVERY'
    authority.mkdir()
    fixture.prepare(authority)
    profile = json.loads((authority/'gateway.json').read_bytes())
    (authority/'gateway.pem').write_text(profile['certificate'])
    from datetime import datetime, timezone
    now = int(time.time())
    timestamp = lambda value: datetime.fromtimestamp(value, timezone.utc).isoformat()
    seed = dict(version=1, family=profile['family'], issued_at=timestamp(now-1), expires_at=timestamp(now+360),
                seeds=[dict(transport='telemost-webrtc', join_url='https://telemost.yandex.ru/j/12345678901234', gateway=profile['gateway'])])
    (authority/'seed.json').write_text(json.dumps(seed))
    issued = subprocess.run(['python3', '-I', str(Path(package)/'cold-provision-locator.pyz'),
                             '--database', str(authority/'access.db'), '--material', str(authority),
                             '--certificate', str(authority/'gateway.pem'), '--state', str(authority),
                             '--node', 'nl-amsterdam-1', '--sequence', '1'], capture_output=True, timeout=10)
    assert issued.returncode == 0, issued.stderr.decode()
    locator = authority/'locator.json'
    expiry = json.loads(base64.b64decode(json.loads(locator.read_bytes())['payload']))['expires_at']
    (authority/'ready.json').write_text(json.dumps(dict(phase='LOCATOR_VERIFIED_SEED_CONNECTED', observed_at=now,
        expires_at=expiry, locator_sha256=hashlib.sha256(locator.read_bytes()).hexdigest())))
    unsigned = authority/'SYNTHETIC-UNSIGNED-NOT-FOR-DELIVERY.apk'
    with zipfile.ZipFile(prebuild) as source, zipfile.ZipFile(unsigned, 'x') as target:
        for item in source.infolist():
            raw = (authority/'anchor.pub').read_bytes() if item.filename == 'assets/control-anchor.pub' else source.read(item.filename)
            target.writestr(item, raw)
    receipt = authority/'fixture-verification.json'
    receipt.write_text(json.dumps(dict(unsigned=True, package='com.familyconnect.app.friends', version_code=120, source_commit='a'*40,
                                      apk_sha256=hashlib.sha256(unsigned.read_bytes()).hexdigest())))
    payload = entries(unsigned)
    accepted = dict(head_sha='a'*40, verification_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                    apk_sha256=hashlib.sha256(unsigned.read_bytes()).hexdigest(),
                    native_sha256=hashlib.sha256(payload['lib/arm64-v8a/libfc_restricted.so']).hexdigest(),
                    anchor_sha256=hashlib.sha256(payload['assets/control-anchor.pub']).hexdigest())
    monkeypatch.setattr(finalizer, 'qualification', lambda: accepted)
    args = SimpleNamespace(unsigned=unsigned, verification=receipt, locator=locator, ready=authority/'ready.json',
        anchor=authority/'anchor.pub', verifier=Path(package)/'cold-provision-entry', node='nl-amsterdam-1',
        zipalign=Path(zipalign), output=authority/'final', handoff_seconds=60)
    result = prepare(args)
    assert result['signed'] is False and result['distributed'] is False
    output = next(args.output.glob('*.apk'))
    assert subprocess.run([zipalign, '-c', '-P', '16', '4', str(output)], capture_output=True, timeout=10).returncode == 0
    assert entries(output)['assets/provisioning/nl-amsterdam-1.json'] == locator.read_bytes()
    with pytest.raises(FileExistsError):
        prepare(args)
