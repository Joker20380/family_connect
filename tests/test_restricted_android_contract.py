from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / 'clients/android/app/src'


def source(name):
    return (ANDROID / 'main/java/com/familyconnect/app' / name).read_text()


def test_existing_owner_and_normal_backends_preserved():
    service = source('ConnectionService.java')
    assert 'engine=restricted' in service
    assert 'ControlOperations.APP.claim(operationOwner)' in service
    assert 'FLAG_DEBUGGABLE' in service and 'ControlMutationGate.managed(this)' in service
    assert 'else start(Transport.parse(requestedTransport))' in service
    assert 'new TcpTunnelEngine' in source('TunnelEngine.java')
    assert 'GoBackend' in source('TunnelEngine.java')
    manifest = ET.parse(ANDROID / 'main/AndroidManifest.xml')
    namespace = '{http://schemas.android.com/apk/res/android}'
    vpn = [item.attrib[namespace+'name'] for item in manifest.findall('.//service')
           if item.attrib.get(namespace+'permission') == 'android.permission.BIND_VPN_SERVICE']
    assert vpn == ['org.amnezia.awg.backend.GoBackend$VpnService', '.TcpVpnService']


def test_underlay_ready_precedes_capture_no_excluded_apps_or_bypass():
    engine = source('RestrictedTunnelEngine.java')
    assert engine.index('NativeRestricted.begin') < engine.index('phase!=1') < engine.index('.establish()') < engine.index('NativeRestricted.attach')
    assert 'TcpVpnService.ready.get' in engine and 'service.revoked=' in engine
    assert '.addRoute("0.0.0.0",0).addRoute("::",0)' in engine
    assert '.addDnsServer("10.79.0.1")' in engine
    assert '.allowBypass(' not in engine and '.addDisallowedApplication(' not in engine
    health = source('ConnectionService.java').split('private void restrictedHealth', 1)[1].split('private void ', 1)[0]
    assert 'failed=true;status="on";healthStatus="unavailable"' in health
    assert 'stopConnection' not in health and 'next()' not in health


def test_stop_closes_native_before_fd_and_service():
    engine = source('RestrictedTunnelEngine.java').split('public void down()', 1)[1]
    assert engine.index('NativeRestricted.stop') < engine.index('tun.close()') < engine.index('service.stopSelf()')
    assert 'stopping||closing' in source('ConnectionService.java')
    assert not (ANDROID / 'main/java/com/familyconnect/app/RestrictedVpnService.java').exists()


def test_diagnostic_entry_is_not_exported_in_release():
    assert 'RestrictedDiagnosticActivity' not in (ANDROID / 'main/AndroidManifest.xml').read_text()
    assert (ANDROID / 'debug/java/com/familyconnect/app/RestrictedDiagnosticActivity.java').is_file()


def test_jni_strings_owned_before_asynchronous_start():
    native = (ROOT / 'pilot/android-restricted/native/main.go').read_text()
    begin = native.split('func fcRestrictedBegin', 1)[1]
    for argument in ('directory', 'control', 'resolver'):
        assert begin.index('strings.Clone('+argument+')') < begin.index('go func()')
    bridge = (ROOT / 'pilot/android-restricted/native/bridge.c').read_text()
    assert 'ReleaseStringUTFChars' in bridge


def test_dedicated_gateway_and_whole_device_use_same_bounded_stream_limit():
    gateway = (ROOT / 'carrier/roombroker/gateway.go').read_text()
    client = (ROOT / 'carrier/wholedevice/session.go').read_text()
    assert 'const DedicatedMaxStreams = tcpforward.MuxMaxStreams' in gateway
    assert 'MuxConfig{MaxStreams: DedicatedMaxStreams}' in gateway
    assert 'MuxConfig{MaxStreams: roombroker.DedicatedMaxStreams}' in client
