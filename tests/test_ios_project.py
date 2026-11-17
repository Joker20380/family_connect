import importlib.util
from pathlib import Path
import plistlib
import pytest
import sys
import datetime
import copy


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ios_project', ROOT / 'clients/ios/project.py')
PROJECT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROJECT)


def test_ios_project_has_real_native_extension_and_unsigned_targets(tmp_path):
    project = PROJECT.generate(ROOT / 'clients/ios', tmp_path, tmp_path / 'native', tmp_path / 'notices')
    text = (project / 'project.pbxproj').read_text()
    assert text.count('com.apple.product-type.app-extension') == 1
    assert text.count('"-lFamilyMesh"') == 2
    assert text.count('"CODE_SIGNING_ALLOWED" = "NO"') == 2
    assert 'PBXCopyFilesBuildPhase' in text
    assert 'PacketBridge.swift' in text
    assert 'PacketTunnelProvider.swift' in text
    assert 'SelfTests.swift' in text
    info = plistlib.loads((tmp_path / 'MeshPacketTunnel.plist').read_bytes())
    assert info['NSExtension']['NSExtensionPointIdentifier'] == 'com.apple.networkextension.packet-tunnel'
    for name in ('MeshPacketTunnel', 'FamilyConnect'):
        entitlement = plistlib.loads((tmp_path / (name+'.entitlements')).read_bytes())
        assert entitlement == {'com.apple.developer.networking.networkextension': ['packet-tunnel-provider'],
                               'keychain-access-groups': ['$(AppIdentifierPrefix)org.familyconnect.mesh.lab.materials']}
        info = plistlib.loads((tmp_path / (name+'.plist')).read_bytes())
        assert info['FCKeychainGroup'] == entitlement['keychain-access-groups'][0]
        assert info['FCTunnelBundleID'] == 'org.familyconnect.mesh.lab.tunnel'


def test_ios_project_generation_is_stable(tmp_path):
    project = PROJECT.generate(ROOT / 'clients/ios', tmp_path, tmp_path / 'native', tmp_path / 'notices')
    first = (project / 'project.pbxproj').read_bytes()
    (project / 'project.pbxproj').unlink()
    project.rmdir()
    PROJECT.generate(ROOT / 'clients/ios', tmp_path, tmp_path / 'native', tmp_path / 'notices')
    assert (project / 'project.pbxproj').read_bytes() == first


def test_development_parameters_and_matching_groups(tmp_path):
    project = PROJECT.generate(ROOT / 'clients/ios', tmp_path, tmp_path / 'native', tmp_path / 'notices',
                               team='TESTTEAM01', bundle='org.example.mesh',
                               app_profile='11111111-1111-1111-1111-111111111111',
                               tunnel_profile='22222222-2222-2222-2222-222222222222')
    text = (project / 'project.pbxproj').read_text()
    assert text.count('"CODE_SIGNING_ALLOWED" = "YES"') == 2
    assert text.count('"DEVELOPMENT_TEAM" = "TESTTEAM01"') == 2
    assert 'CodeSignOnCopy' in text
    for name in ('MeshPacketTunnel', 'FamilyConnect'):
        info = plistlib.loads((tmp_path / (name+'.plist')).read_bytes())
        assert info['FCKeychainGroup'] == '$(AppIdentifierPrefix)org.example.mesh.materials'
        assert info['FCTunnelBundleID'] == 'org.example.mesh.tunnel'


@pytest.mark.parametrize('kwargs', [{'bundle': 'com.apple.managed.vpn.shared'}, {'bundle': 'bad'},
                                    {'team': 'short'}, {'team': 'TESTTEAM01'}, {'app_profile': 'private.p12'}])
def test_development_rejects_inconsistent_parameters(tmp_path, kwargs):
    with pytest.raises(ValueError):
        PROJECT.generate(ROOT / 'clients/ios', tmp_path, tmp_path, tmp_path, **kwargs)


def test_provisioning_grants_model(monkeypatch):
    monkeypatch.setitem(sys.modules, 'project', PROJECT)
    spec = importlib.util.spec_from_file_location('ios_development', ROOT / 'clients/ios/development.py')
    development = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(development)
    profile = {'TeamIdentifier': ['TESTTEAM01'], 'ApplicationIdentifierPrefix': ['OTHERPRE01'],
               'ExpirationDate': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
               'ProvisionedDevices': ['synthetic-device-only'],
               'Entitlements': {'get-task-allow': True, 'application-identifier': 'OTHERPRE01.org.example.mesh',
                                'com.apple.developer.team-identifier': 'TESTTEAM01',
                                'com.apple.developer.networking.networkextension': ['packet-tunnel-provider'],
                                'keychain-access-groups': ['OTHERPRE01.org.example.mesh.materials']}}
    def check(value):
        return development.validate_profile(value, team='TESTTEAM01', bundle='org.example.mesh', service='org.example.mesh.materials')
    assert check(profile) == 'OTHERPRE01'
    for field, value in [('get-task-allow', False), ('application-identifier', 'OTHERPRE01.wrong.bundle'),
                         ('com.apple.developer.team-identifier', 'WRONGTEAM1'),
                         ('com.apple.developer.networking.networkextension', []),
                         ('keychain-access-groups', ['com.apple.managed.vpn.shared'])]:
        invalid = copy.deepcopy(profile)
        invalid['Entitlements'][field] = value
        with pytest.raises(ValueError):
            check(invalid)
    for field, value in [('TeamIdentifier', ['WRONGTEAM1']), ('ProvisionedDevices', []),
                         ('ExpirationDate', datetime.datetime(2000, 1, 1)), ('ApplicationIdentifierPrefix', [])]:
        invalid = copy.deepcopy(profile)
        invalid[field] = value
        with pytest.raises(ValueError):
            check(invalid)
