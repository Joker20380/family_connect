import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_accepted_messenger_closure_and_explicit_platform_delta():
    manifest = json.loads((ROOT / 'clients/shared/android106-messenger.json').read_text())
    assert manifest['source_inventory_sha256'] == '8574228fc809fdbd67b3d92680e09c979fe930599a47e4ed1b47fd30f872ed0c'
    assert set(manifest['local_adaptations']) == {'messenger/routed.py'}
    for relative, accepted in manifest['accepted_modules'].items():
        expected = manifest['local_adaptations'].get(relative, {}).get('sha256', accepted)
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    patch = (ROOT / manifest['local_adaptations']['messenger/routed.py']['patch']).read_text()
    assert "+    ROUTES = ('DIRECT', 'EXISTING_EXIT', 'SERVICE_ONLY')" in patch


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
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    assert contract['polling']['feed_seconds'] == 30
