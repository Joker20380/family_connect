from pathlib import Path
import importlib.util
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'clients/android/app/src/main/java/com/familyconnect/app'


def source(name):
    return (MAIN / (name + '.java')).read_text()


def test_only_existing_service_owns_automatic_tuns():
    owner = source('AutomaticVpnOwner')
    assert 'TcpVpnService.ready.get' in owner
    assert '.addRoute("0.0.0.0",0).addRoute("::",0)' in owner
    assert '.allowBypass(' not in owner and '.addDisallowedApplication(' not in owner
    replace = owner.split('ParcelFileDescriptor replace', 1)[1]
    assert replace.index('builder.establish()') < replace.index('previous.close()')
    engine = source('AutomaticNormalEngine')
    assert 'new GoBackend(' not in engine and 'GoBackend.awgTurnOn' in engine
    assert 'ParcelFileDescriptor.dup' in engine and '.protect(socket4)' in engine
    assert 'NativeTcp.start(owner.replace(builder).getFd(),profile,owner.service())' in engine
    assert 'stopSelf' not in engine
    assert 'if(awg<0)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.INTERNAL)' in engine
    assert 'tcp==-2?ConnectivityOrchestrator.Failure.CONFIGURATION:ConnectivityOrchestrator.Failure.INTERNAL' in engine


def test_failed_guard_precedes_engine_cleanup_and_does_not_skip_it():
    host = source('AutomaticConnection')
    close = host.split('public void closeCandidate()', 1)[1].split('public void release()', 1)[0]
    assert close.index('owner.block()') < close.index('candidate.down()') < close.index('throw blocked')
    assert 'candidate=null' in close
    core = source('ConnectivityOrchestrator')
    finish = core.split('private void finish', 1)[1].split('void disconnect()', 1)[0]
    assert 'host.release()' not in finish
    assert 'State.FAILED' in finish and 'host.closeCandidate()' in finish


def test_automatic_tcp_does_not_advertise_unverified_ipv6_exit():
    tcp = source('AutomaticNormalEngine').split('if(transport==Transport.TCP)', 1)[1].split('Config config=', 1)[0]
    assert '.addAddress(source,32)' in tcp
    assert '.addRoute("0.0.0.0",0).addRoute("::",0)' in tcp
    assert 'fd79:' not in tcp
    assert '.allowBypass(' not in tcp and '.addDisallowedApplication(' not in tcp


def test_diagnostic_io_cannot_skip_native_stop_and_provisioning_reads_are_bounded():
    cleanup = source('RestrictedTunnelEngine').split('public void down()', 1)[1]
    assert 'try { evidence(); }catch(Exception ignored){}' in cleanup
    assert cleanup.index('evidence()') < cleanup.index('NativeRestricted.stop(handle)')
    assert 'connection.setReadTimeout(remaining(15000));int count=input.read(buffer)' in source('FriendsAccessAndroid')


def test_no_live_descriptor_in_preference_or_events():
    host = source('AutomaticConnection')
    remember = host.split('public void remember', 1)[1].split('public void event', 1)[0]
    assert 'Transport.parse(id)' in remember
    assert 'putString("normal_hint",id)' in remember
    for forbidden in ('JoinURL', 'join_url', 'getMessage()', 'destination', 'room_url'):
        assert forbidden not in host
    assert 'MAX_EVENTS=128' in source('ConnectivityOrchestrator')


def test_automatic_cached_path_has_no_fake_control_failure_request():
    native = (ROOT / 'pilot/android-restricted/native/main.go').read_text()
    assert 'if control == "auto"' in native and 'wholedevice.OpenCached(' in native
    cached = (ROOT / 'carrier/wholedevice/session.go').read_text().split('func OpenCached(', 1)[1]
    assert 'BootstrapDirectory(' not in cached
    assert cached.index('cache.Load(time.Now())') < cached.index('bootstrap.Recover(')
    assert 'descriptor.JoinURL' in cached and 'roombroker.BindClient' in cached


def test_debug_fault_controls_are_not_release_entry_points():
    manifest = (ROOT / 'clients/android/app/src/main/AndroidManifest.xml').read_text()
    assert 'OrchestratorDiagnosticActivity' not in manifest
    host = source('AutomaticConnection')
    assert 'if(debug&&' in host and 'FLAG_DEBUGGABLE' in host
    assert 'START_NOT_STICKY' in source('ConnectionService')
    assert 'if(automatic)startAutomatic' in source('ConnectionService')


def load_runner():
    directory = ROOT / 'pilot/android-restricted'
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location('orchestrator_normal', directory / 'orchestrator_normal.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_runner_rejects_missing_alternate_and_extra_diagnostic_fields():
    runner = load_runner()
    attempted = {'event': 'candidate_attempted', 'candidate': 'tcp', 'state': 'CONNECTING', 'elapsed_ms': 1}
    ready = {'event': 'time_to_connected', 'candidate': 'tcp', 'state': 'CONNECTED', 'elapsed_ms': 100}
    assert runner.validate_events([attempted, ready], ['tcp']) == [100]
    with pytest.raises(RuntimeError):
        runner.validate_events([attempted, ready], ['awg', 'tcp'])
    with pytest.raises(RuntimeError):
        runner.validate_events([attempted, ready | {'destination': 'forbidden'}], ['tcp'])


def test_controlled_browser_localization_does_not_accept_url_or_error():
    runner = load_runner()
    text = 'example.org Este dominio se utiliza para ejemplos de documentación'
    assert runner.browser_content(text, 'example.org')
    assert not runner.browser_content('example.org', 'example.org')
    assert not runner.browser_content(text + ' ERR_CONNECTION_RESET', 'example.org')
    assert not runner.browser_content(text, 'example.com')
