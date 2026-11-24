import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pytest


ROOT = Path(__file__).resolve().parents[1]
MESSENGER = json.loads((ROOT / 'clients/shared/android106-messenger.json').read_text())
SUPPORT = json.loads((ROOT / 'clients/shared/support1-messenger.json').read_text())


@pytest.mark.parametrize('relative,accepted', MESSENGER['accepted_modules'].items())
def test_each_accepted_messenger_module_with_explicit_deltas(relative, accepted):
    expected = MESSENGER['local_adaptations'].get(relative, {}).get('sha256', accepted)
    expected = SUPPORT['modules'].get(relative, {}).get('sha256', expected)
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize('relative,expected', {**MESSENGER['additional_modules'], **SUPPORT['additional_modules']}.items())
def test_each_additional_dependency(relative, expected):
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_accepted_messenger_closure_and_explicit_platform_delta():
    manifest = json.loads((ROOT / 'clients/shared/android106-messenger.json').read_text())
    assert manifest['source_inventory_sha256'] == '8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c'
    assert set(manifest['local_adaptations']) == {'messenger/routed.py', 'messenger/local.py', 'messenger/store.py'}
    assert manifest['subsequent_deltas'] == ['clients/shared/support1-messenger.json']
    assert SUPPORT['accepted_commit'] == '10d353d8d219b1e23e3cbf6a1e66c0ca8fe1824f'
    assert set(SUPPORT['modules']) == {'messenger/chat.py', 'messenger/local.py', 'messenger/store.py'}
    assert set(SUPPORT['additional_modules']) == {'messenger/support.py'}
    assert hashlib.sha256((ROOT / SUPPORT['patch']).read_bytes()).hexdigest() == SUPPORT['patch_sha256']
    modules = set(manifest['accepted_modules']) | set(manifest['additional_modules']) | set(SUPPORT['additional_modules'])
    for relative in modules:
        for node in ast.walk(ast.parse((ROOT / relative).read_text())):
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                names = [node.module] if node.module else [alias.name for alias in node.names]
                assert all('messenger/' + name.replace('.', '/') + '.py' in modules for name in names), relative
    patch = (ROOT / manifest['local_adaptations']['messenger/routed.py']['patch']).read_text()
    assert "+    ROUTES = ('DIRECT', 'EXISTING_EXIT', 'SERVICE_ONLY')" in patch


def test_subscription_adaptation_reverses_to_unchanged_accepted106_sources(tmp_path):
    manifest = json.loads((ROOT / 'clients/shared/android106-messenger.json').read_text())
    notifications = json.loads((ROOT / 'clients/shared/android106-notifications.json').read_text())
    for name in set(manifest['accepted_modules']) | set(manifest['additional_modules']) | set(SUPPORT['additional_modules']):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, tmp_path / name)
    subprocess.run(['git', 'apply', '--reverse', str(ROOT / SUPPORT['patch'])],
                   cwd=tmp_path, check=True, capture_output=True)
    for name, hashes in SUPPORT['modules'].items():
        expected = manifest['local_adaptations'].get(name, {}).get('sha256', manifest['accepted_modules'][name])
        assert hashes['before_sha256'] == expected
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == expected
    assert not (tmp_path / 'messenger/support.py').exists()
    for name in ('messenger/local.py', 'messenger/store.py'):
        assert manifest['local_adaptations'][name]['patch'] == 'clients/shared/subscription119-messenger.patch'
    subprocess.run(['git', 'apply', '--reverse', str(ROOT / 'clients/shared/subscription119-messenger.patch')],
                   cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'apply', '--reverse', str(ROOT / 'clients/shared/android106-messenger.patch')],
                   cwd=tmp_path, check=True, capture_output=True)
    for name in manifest['accepted_modules']:
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == manifest['accepted_modules'][name]
    assert set(notifications['local_adaptations']) == {'messenger/store.py'}
    assert notifications['local_adaptations']['messenger/store.py']['sha256'] == manifest['local_adaptations']['messenger/store.py']['sha256']
    assert notifications['accepted_sources']['messenger/store.py'] == manifest['accepted_modules']['messenger/store.py']
    assert notifications['subsequent_deltas'] == manifest['subsequent_deltas']
    assert set(manifest['additional_modules']) == {'messenger/subscription_view.py'}
    for name, expected in manifest['additional_modules'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


def test_gtk_chat_strings_are_verbatim_accepted_resource_values():
    contract = json.loads((ROOT / 'clients/shared/android106-ui.json').read_text())
    tree = ast.parse((ROOT / 'clients/desktop/chat_strings.py').read_text())
    assignment = next(item for item in tree.body if isinstance(item, ast.Assign))
    strings = ast.literal_eval(assignment.value)
    assert len(strings) == 89
    for name, values in strings.items():
        assert values == (contract['strings']['ru'][name], contract['strings']['en'][name])


def test_announcement_contract_pins_existing_server_authority_and_exact_actions():
    contract = json.loads((ROOT / 'clients/shared/android106-announcements.json').read_text())
    assert contract['source_inventory_sha256'] == '8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c'
    assert len(contract['accepted_sources']) == 7
    for name, expected in contract['accepted_sources'].items():
        if not name.startswith('clients/android/'):
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    assert contract['actions'] == ['list', 'publish', 'edit']
    assert contract['publication'] == dict(kind='information', platforms=['android', 'windows', 'linux'], days=30)
    assert set(contract['edit_fields']) == {'id', 'revision', 'request_id', 'title', 'body'}


def test_linux_voice_limits_and_codec_ids_match_accepted_contract():
    from provisioning.chat_audio import MAX_BYTES, MAX_MILLIS, OPUS, RADIO
    contract = json.loads((ROOT / 'clients/shared/android106-voice.json').read_text())
    assert contract['source_inventory_sha256'] == '8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c'
    assert len(contract['accepted_sources']) == 9
    assert MAX_BYTES == contract['limits']['max_bytes'] == 131072
    assert MAX_MILLIS == contract['limits']['max_millis'] == 60000
    assert OPUS == 16 and set(RADIO) == {7, 8, 9}
    for mode, (library_mode, samples, size) in RADIO.items():
        expected = contract['modes'][str(mode)]
        assert (library_mode, samples, size) == (expected['library_mode'], expected['samples'], expected['bytes'])


def test_notification_reference_preserves_shared_sources_and_records_platform_limits():
    contract = json.loads((ROOT / 'clients/shared/android106-notifications.json').read_text())
    assert contract['source_inventory_sha256'] == '8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c'
    assert len(contract['accepted_sources']) == 8
    for name, expected in contract['accepted_sources'].items():
        if name.startswith('messenger/'):
            expected = contract['local_adaptations'].get(name, {}).get('sha256', expected)
            expected = SUPPORT['modules'].get(name, {}).get('sha256', expected)
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    assert contract['polling']['feed_seconds'] == 30
