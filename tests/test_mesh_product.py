import ast
from pathlib import Path
import re

from scripts import correlate_restricted
from test_restricted_correlation import SUPPORT, fixture


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'pilot/android-restricted/mesh-product.patch'


def test_approved_android_overlay_changes_only_presentation():
    patch = PATCH.read_text()
    paths = re.findall(r'^\+\+\+ b/(.+)$', patch, re.MULTILINE)
    assert set(paths) == {
        'clients/android/app/src/main/java/com/familyconnect/app/FriendsActivity.java',
        'clients/android/app/src/main/java/com/familyconnect/app/DiagnosticRing.java',
        'clients/android/app/src/main/java/com/familyconnect/app/TransportPresentation.java',
        'clients/android/app/src/main/res/values/connection_terminal.xml',
        'clients/android/app/src/main/res/values-ru/connection_terminal.xml',
        'clients/android/app/src/test/java/com/familyconnect/app/TransportPresentationTest.java',
        'clients/android/app/src/test/java/com/familyconnect/app/DiagnosticRingTest.java',
    }
    changed = '\n'.join(line for line in patch.splitlines() if line[:1] in ('+', '-') and line[:3] not in ('+++', '---'))
    assert all(token not in changed for token in ('putString(', 'getPreferences(', 'setSelection(', 'setOnItemSelectedListener(',
        'new Intent(', 'startForegroundService(', 'setPadding(', 'setTextSize(', 'setLayoutParams(', 'setTypeface('))
    assert '{"telemost",TransportPresentation.MESH}' in changed
    assert '{"mesh",' not in changed
    assert 'Opening MESH carrier' in changed and 'Открытие канала MESH' in changed


def test_diagnostic_catalog_is_additive_for_existing_correlator():
    client, server = fixture()
    before = correlate_restricted.correlate([client], server, SUPPORT)
    client['ring']['transport_metadata'] = dict(schema=1, restricted=dict(name='MESH',
        implementation='restricted', selection_id='telemost', carrier='VP8/RTP', provider='Telemost'))
    assert correlate_restricted.correlate([client], server, SUPPORT) == before


def test_linux_does_not_advertise_a_nonexistent_media_backend():
    tree = ast.parse((ROOT / 'clients/desktop/app.py').read_text())
    transports = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == 'TRANSPORTS' for target in node.targets))
    assert transports == (('awg', 'AWG 3.1'), ('tcp', 'TCP REALITY'))
    backend = (ROOT / 'clients/desktop/backend.py').read_text()
    assert 'class Linux:' in backend and 'class LinuxTCP(Linux):' in backend
    assert "awg_helper='/usr/local/lib/family-connect-awg/helper'" in backend


def test_windows_does_not_advertise_a_nonexistent_media_backend():
    ui = (ROOT / 'clients/windows/MainForm.cs').read_text()
    assert 'mode.Items.AddRange(new object[]{"TCP REALITY","AWG 3.1"})' in ui
    broker = (ROOT / 'clients/windows/Broker.cs').read_text()
    assert 'case "connect-awg":' in broker and 'case "connect-tcp":' in broker
    assert 'case "connect-mesh":' not in broker and 'case "connect-telemost":' not in broker


def test_presentation_never_becomes_a_wire_protocol_or_persistence_migration():
    source = (ROOT / 'clients/android/app/src/main/java/com/familyconnect/app/TransportPresentation.java').read_text()
    assert '"selection_id","telemost"' in source and '"implementation","restricted"' in source
    assert all(token not in source for token in ('SharedPreferences', 'DeviceIdentity', 'NetworkProvisioningState',
        'mesh/1', 'private_key', 'room_url', 'token', 'Executor', 'Socket'))
