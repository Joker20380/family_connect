import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from scripts import cold_field_preflight as gate
from scripts import prepare_cold_field_apk as finalizer


def synthetic_inputs(tmp_path, monkeypatch):
    args = SimpleNamespace(**{name: tmp_path/name for name in
        ('unsigned', 'verification', 'anchor', 'verifier', 'aapt', 'zipalign', 'apksigner')})
    args.anchor.write_bytes(b'synthetic-anchor')
    args.verifier.write_bytes(b'synthetic-verifier')
    with zipfile.ZipFile(args.unsigned, 'w') as archive:
        archive.writestr('assets/control-anchor.pub', args.anchor.read_bytes())
        archive.writestr('lib/arm64-v8a/libfc_restricted.so', b'synthetic-native')
    receipt = dict(unsigned=True, package=finalizer.PACKAGE, version_code=120,
                   source_commit='a'*40, apk_sha256=finalizer.digest(args.unsigned.read_bytes()))
    args.verification.write_text(json.dumps(receipt, indent=2)+'\n')
    accepted = dict(head_sha='a'*40, verification_sha256=finalizer.digest(args.verification.read_bytes()),
                    apk_sha256=receipt['apk_sha256'], native_sha256=finalizer.digest(b'synthetic-native'),
                    anchor_sha256=finalizer.digest(args.anchor.read_bytes()),
                    verifier_sha256=finalizer.digest(args.verifier.read_bytes()))
    monkeypatch.setattr(finalizer, 'qualification', lambda: accepted)
    monkeypatch.setattr(gate.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(gate.subprocess, 'check_output', lambda *args, **kwargs:
        "package: name='com.familyconnect.app.friends' versionCode='120' versionName='0.1.18-beta120'\n"
        "sdkVersion:'27'\nnative-code: 'arm64-v8a'\n"
        "launchable-activity: name='com.familyconnect.app.FriendsActivity'\n")
    return args


def test_original_receipt_passes_before_entry_and_namespace_is_not_application_id(tmp_path, monkeypatch):
    args = synthetic_inputs(tmp_path, monkeypatch)
    starts = []
    stops = []
    receipt = gate.run_field(args, lambda verified: starts.append(verified['launcher']),
                             lambda verified, entry: verified, stops.append)
    assert starts == ['com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity']
    assert receipt['entry_started'] is False
    assert receipt['state'] == 'PREFLIGHT_PASS_NO_ENTRY_STARTED'
    assert stops == [None]


@pytest.mark.parametrize('corrupt', ['derived-receipt', 'apk', 'verifier', 'anchor', 'tool'])
def test_bad_inputs_never_start_entry(tmp_path, monkeypatch, corrupt):
    args = synthetic_inputs(tmp_path, monkeypatch)
    if corrupt == 'derived-receipt':
        args.verification.write_text(json.dumps(json.loads(args.verification.read_bytes())))
    elif corrupt == 'tool':
        monkeypatch.setattr(gate.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=127))
    else:
        getattr(args, 'unsigned' if corrupt == 'apk' else corrupt).write_bytes(b'changed')
    starts = []
    with pytest.raises(ValueError):
        gate.run_field(args, starts.append, lambda *args: None, lambda entry: None)
    assert starts == []


def test_operation_failure_keeps_cleanup(tmp_path, monkeypatch):
    args = synthetic_inputs(tmp_path, monkeypatch)
    stops = []
    def fail(*args):
        raise RuntimeError('synthetic operation failure')
    with pytest.raises(RuntimeError):
        gate.run_field(args, lambda verified: 'synthetic-invocation', fail, stops.append)
    assert stops == ['synthetic-invocation']


def test_manifest_and_package_manager_must_agree():
    expected = 'com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity'
    assert gate.installed_launcher(expected+'\n', expected) == expected
    for wrong in ('com.familyconnect.app.friends/.FriendsActivity', '', 'No activity found'):
        with pytest.raises(ValueError):
            gate.installed_launcher(wrong, expected)
    for badging in ("package: name='other'", "package: name='com.familyconnect.app.friends'"):
        with pytest.raises(ValueError):
            gate.launcher(badging)


@pytest.mark.parametrize('change', [{}, {'stopped': True}, {'invocation_id': 'b'*32},
    {'main_pid': 0}, {'active_state': 'inactive'}, {'observed_at': 1200}])
def test_connect_requires_fresh_live_same_invocation(change):
    status = dict(invocation_id='a'*32, active_state='active', sub_state='running',
                  main_pid=42, stopped=False, observed_at=1210)
    ready = dict(invocation_id='a'*32, phase='LOCATOR_VERIFIED_SEED_CONNECTED',
                 locator_sha256='c'*64, expires_at=1500, observed_at=1200)
    locator = dict(locator_sha256='c'*64, expires_at=1500)
    if change:
        with pytest.raises(ValueError):
            gate.check_entry(dict(status, **change), ready, locator, 'a'*32, now=1211)
    else:
        assert gate.check_entry(status, ready, locator, 'a'*32, now=1211)['connect_not_after'] == 1300
        with pytest.raises(ValueError):
            gate.check_entry(dict(status, observed_at=1301), dict(ready, observed_at=1301), locator, 'a'*32, now=1301)
        with pytest.raises(ValueError):
            gate.check_entry(status, dict(ready, invocation_id='d'*32), locator, 'a'*32, now=1211)


def test_consolidated_qualification_requires_independently_pinned_complete_descriptor(tmp_path):
    path = tmp_path/'qualified121.json'
    value = dict(state='ANDROID_RELEASE_CI_ACCEPTED', version_code=121, version='0.1.18-beta121',
                 package=finalizer.PACKAGE, signer_sha256=finalizer.SIGNER, head_sha='a'*40,
                 run_id=1, android_job_id=2, artifact_id=3)
    value.update({name: 'b'*64 for name in ('verification_sha256', 'apk_sha256', 'native_sha256',
                 'anchor_sha256', 'artifact_sha256', 'verifier_sha256')})
    path.write_text(json.dumps(value))
    args = SimpleNamespace(qualification=path, qualification_sha256=finalizer.digest(path.read_bytes()))
    assert finalizer.release_inputs(args)['version_code'] == 121
    path.write_text(json.dumps(dict(value, version_code=122)))
    with pytest.raises(ValueError, match='digest'):
        finalizer.release_inputs(args)
    args.qualification_sha256 = finalizer.digest(path.read_bytes())
    with pytest.raises(ValueError, match='consolidated'):
        finalizer.release_inputs(args)
    assert finalizer.release_inputs(SimpleNamespace())['version_code'] == 120


def test_historical_qualification_bytes_unchanged():
    original = Path(finalizer.__file__).with_name('cold-field-qualified.json').read_bytes()
    assert json.loads(original)['head_sha'] == '55525859465ff4713196db7206129ad840f67cb3'
    assert json.loads(original)['verification_sha256'] == '48eab8c49462e3feb8c1d819db037c909ea92129eadc5915f073436275f466bb'


def test_upgrade_fixtures_keep_exact_119_and_120_vault_formats():
    root = Path(__file__).resolve().parents[1]/'clients/android/app/src/main/java/com/familyconnect/app'
    historical = {
        'FriendsIdentityVault.java': '5a99173963eb04be4e3e302d563795075eccc75c35caa1c565175dbe0817a7e9',
        'ChatKeyVault.java': '620c8527ebba2519944c3106052b29d2a75070c55355a5bb096325cf0ae6559f',
        'ChatKeyEnvelope.java': '370a0e6419dbb87fb3a861569ce5082fbb288461098dfcadae19458e8759c731',
        'ChatStoreCipher.java': '8eade0617865ebab0073861333aa13a3a599904d85addfe28c7d66d30fcb308d',
    }
    for name, expected in historical.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == expected
