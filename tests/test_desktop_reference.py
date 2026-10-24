import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest

from scripts.verify_desktop_reference import MANIFEST, READINESS_MANIFEST, RNS_PUBLIC_SOURCES, digest, local_path, verify


def test_gtk_connection_state_labels_are_exact_reference_text():
    import ast
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'clients/desktop/app.py').read_text())
    assignment=next(item for item in tree.body if isinstance(item,ast.Assign) and
                    any(isinstance(target,ast.Name) and target.id=='STATE_LABELS' for target in item.targets))
    labels=ast.literal_eval(assignment.value)
    contract=json.loads((root/'clients/shared/android106-ui.json').read_text())
    for state,key in {'DISCONNECTED':'off','CONNECTING':'connecting','CONNECTED':'on',
                      'RESTORING':'restoring','STOPPING':'ui_disconnecting','FAILED':'unable_connect'}.items():
        assert labels[state]==tuple(contract['strings'][language][key] for language in ('ru','en'))
    assignment=next(item for item in tree.body if isinstance(item,ast.Assign) and
                    any(isinstance(target,ast.Name) and target.id=='NAV_LABELS' for target in item.targets))
    labels=ast.literal_eval(assignment.value)
    for page,key in {'status':'dashboard_status','messenger':'dashboard_chats',
                     'route':'dashboard_route_short','settings':'dashboard_settings_short'}.items():
        assert labels[page]==tuple(contract['strings'][language][key] for language in ('ru','en'))


def test_readiness_semantic_port_uses_exact_accepted_sources():
    root = Path(__file__).resolve().parents[1]
    reference = json.loads((root / MANIFEST).read_text())
    contract = json.loads((root / READINESS_MANIFEST).read_text())
    assert contract['apk_sha256'] == reference['reference']['apk_sha256']
    assert contract['source_inventory_sha256'] == reference['reference']['source_inventory_sha256']
    for path, expected in contract['source_files'].items():
        assert reference['android_ui_and_handlers'][path] == expected
    assert set(contract['rns_source_files']) == set(RNS_PUBLIC_SOURCES)
    for accepted, public in RNS_PUBLIC_SOURCES.items():
        assert digest(local_path(root, public)) == contract['rns_source_files'][accepted]
    for path in contract['implementation'].values():
        assert local_path(root, path).is_file()
    assert contract['invariants']['profiles'] == ['P0', 'P1']
    assert not contract['invariants']['native_proposal_is_durable']


def test_supported_shared_sources_match_accepted_inventory():
    assert verify()["result"] == "PASS"


def test_restricted_chat_contract_has_exact_services_and_bounds():
    from scripts.verify_desktop_reference import ROOT
    contract = json.loads((ROOT / 'clients/shared/android106-chat.json').read_text())
    reference = json.loads((ROOT / MANIFEST).read_text())
    assert contract['source_inventory_sha256'] == reference['reference']['source_inventory_sha256']
    assert contract['services'] == ['chat-api', 'chat-mailbox']
    assert contract['api_paths'] == ['/friends/chat/challenge', '/friends/chat/register']
    assert contract['maximum_leases'] == 8 and contract['maximum_session_service_streams'] == 4
    assert contract['authorization_statuses'] == [400, 401, 403] and contract['conflict_status'] == 409
    assert (contract['request_bytes'], contract['response_bytes'], contract['maximum_duration_ms']) == (8192, 16384, 30000)
    assert contract['redirects'] is False and contract['proxy_environment'] is False
    assert contract['api_origin'] == 'https://185.251.89.19:8443'
    for path in contract['implementation']:
        assert local_path(ROOT, path).is_file()


@pytest.mark.parametrize("name", ["../escape", "/etc/passwd", "carrier/../../escape", "..\\escape"])
def test_manifest_paths_cannot_escape(tmp_path, name):
    with pytest.raises(ValueError):
        local_path(tmp_path, name)


def test_manifest_rejects_symlink_escape(tmp_path):
    (tmp_path / "link").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        local_path(tmp_path, "link/escape")


def test_source_drift_is_not_a_match(public_reference):
    source = public_reference / "core.go"
    source.write_text("package core\n")
    path = public_reference / MANIFEST
    manifest = json.loads(path.read_text())
    manifest['shared_sources'] = {'core.go': {'sha256': digest(source)}}
    path.write_text(json.dumps(manifest))
    assert verify(public_reference)["result"] == "PASS"
    source.write_text("package changed\n")
    assert verify(public_reference)["failures"] == ["core.go"]
    source.unlink()
    assert verify(public_reference)["failures"] == ["core.go"]


def test_experimental_build_tags_are_rejected(tmp_path):
    manifest = tmp_path / MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"schema": 1, "build_tags": ["fc_messenger_lab"]}))
    with pytest.raises(ValueError):
        verify(tmp_path)


def test_visual_contract_is_reproducible_when_capsule_is_available():
    from scripts.extract_desktop_contract import extract
    from scripts.verify_desktop_reference import ROOT

    manifest = json.loads((ROOT / MANIFEST).read_text())
    if not (ROOT / manifest["reference"]["source"]).exists():
        pytest.skip("reference capsule is not distributed in CI")
    contract = json.loads((ROOT / "clients/shared/android106-ui.json").read_text())
    assert extract() == contract
    assert contract["palette"]["background"] == "#071211"
    assert contract["navigation"] == ["home", "messenger", "route", "settings"]


@pytest.fixture
def public_reference(tmp_path):
    root = Path(__file__).resolve().parents[1]
    reference = json.loads((root / MANIFEST).read_text())['reference']
    manifest = dict(schema=1, build_tags=[], desktop_adaptations={}, shared_sources={},
                    android_ui_and_handlers={}, reference=reference)
    for name in (str(READINESS_MANIFEST), *RNS_PUBLIC_SOURCES.values(), 'scripts/verify_desktop_reference.py'):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    (tmp_path / MANIFEST).write_text(json.dumps(manifest))
    return tmp_path


@pytest.mark.parametrize('public', RNS_PUBLIC_SOURCES.values())
@pytest.mark.parametrize('change', ['missing', 'changed'])
def test_public_readiness_sources_fail_closed(public_reference, public, change):
    target = public_reference / public
    if change == 'missing':
        target.unlink()
    else:
        target.write_bytes(b'changed')
    result = verify(public_reference)
    assert result['result'] == 'FAIL'
    assert result['failures'] == ['readiness_public/' + public]
    assert result['capsule_files'] is None


@pytest.mark.parametrize('field,reason', [('apk_sha256', 'readiness_apk'),
                                        ('source_inventory_sha256', 'readiness_inventory')])
def test_readiness_metadata_must_match_main_reference(public_reference, field, reason):
    path = public_reference / READINESS_MANIFEST
    readiness = json.loads(path.read_text())
    readiness[field] = '0' * 64
    path.write_text(json.dumps(readiness))
    assert verify(public_reference)['failures'] == [reason]


@pytest.fixture
def synthetic_capsule(public_reference):
    root = public_reference
    manifest = json.loads((root / MANIFEST).read_text())
    reference = manifest['reference']
    reference.update(source='synthetic/source', source_inventory='synthetic/inventory.json',
                     apk='synthetic/app.apk', source_count=len(RNS_PUBLIC_SOURCES))
    inventory = {}
    for accepted, public in RNS_PUBLIC_SOURCES.items():
        target = root / reference['source'] / accepted
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / public).read_bytes())
        inventory[accepted] = digest(target)
    inventory_path = root / reference['source_inventory']
    inventory_path.write_text(json.dumps(inventory))
    reference['source_inventory_sha256'] = digest(inventory_path)
    native = b'synthetic native, not an accepted Android binary'
    with zipfile.ZipFile(root / reference['apk'], 'w') as archive:
        archive.writestr('lib/arm64-v8a/libfc_restricted.so', native)
    reference.update(apk_sha256=digest(root / reference['apk']),
                     restricted_native_sha256=hashlib.sha256(native).hexdigest())
    readiness_path = root / READINESS_MANIFEST
    readiness = json.loads(readiness_path.read_text())
    readiness.update(apk_sha256=reference['apk_sha256'],
                     source_inventory_sha256=reference['source_inventory_sha256'])
    readiness_path.write_text(json.dumps(readiness))
    trace = root / 'synthetic/auto-trace.json'
    trace.write_text('[]')
    for name in ('voice', 'chat', 'notifications', 'announcements', 'auto'):
        contract = dict(source_inventory_sha256=reference['source_inventory_sha256'], accepted_sources={})
        if name == 'auto':
            contract['reference_trace'] = dict(path='synthetic/auto-trace.json', sha256=digest(trace))
        (root / f'clients/shared/android106-{name}.json').write_text(json.dumps(contract))
    (root / MANIFEST).write_text(json.dumps(manifest))
    return root


def test_synthetic_capsule_is_a_separate_complete_verification(synthetic_capsule):
    assert verify(synthetic_capsule)['capsule_files'] is None
    result = verify(synthetic_capsule, capsule=True)
    assert result['result'] == 'PASS' and not result['failures']
    assert result['capsule_files'] == len(RNS_PUBLIC_SOURCES)


@pytest.mark.parametrize('accepted', RNS_PUBLIC_SOURCES)
def test_readiness_rns_pin_must_match_verified_inventory(synthetic_capsule, accepted):
    root = synthetic_capsule
    public = root / RNS_PUBLIC_SOURCES[accepted]
    public.write_bytes(b'synthetic replacement, not accepted bytes')
    path = root / READINESS_MANIFEST
    readiness = json.loads(path.read_text())
    readiness['rns_source_files'][accepted] = digest(public)
    path.write_text(json.dumps(readiness))
    assert verify(root)['result'] == 'PASS'
    result = verify(root, capsule=True)
    assert result['result'] == 'FAIL'
    assert result['failures'] == ['readiness_reference/' + accepted]


@pytest.mark.parametrize('missing', ['source_inventory', 'apk', 'source'])
@pytest.mark.parametrize('change', ['missing', 'changed'])
def test_explicit_capsule_cli_rejects_missing_or_changed_inputs(synthetic_capsule, missing, change):
    root = synthetic_capsule
    reference = json.loads((root / MANIFEST).read_text())['reference']
    target = root / reference[missing]
    reason = missing
    if missing == 'source':
        accepted = 'clients/android/app/src/main/python/fc_rns_transport.py'
        target /= accepted
        reason = 'capsule/' + accepted
    if change == 'missing':
        target.unlink()
    else:
        target.write_bytes(b'not the pinned input')
    assert verify(root)['result'] == 'PASS'
    result = subprocess.run([sys.executable, str(root / 'scripts/verify_desktop_reference.py'), '--capsule'],
                            cwd=root, capture_output=True, text=True, timeout=20)
    assert result.returncode == 1, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output['result'] == 'FAIL' and reason in output['failures']


def test_capsule_native_hash_remains_required(synthetic_capsule):
    path = synthetic_capsule / MANIFEST
    manifest = json.loads(path.read_text())
    manifest['reference']['restricted_native_sha256'] = '0' * 64
    path.write_text(json.dumps(manifest))
    assert verify(synthetic_capsule, capsule=True)['failures'] == ['restricted_native']
