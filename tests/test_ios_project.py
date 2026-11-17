import importlib.util
from pathlib import Path
import plistlib
import pytest


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
