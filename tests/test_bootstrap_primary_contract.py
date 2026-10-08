from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / 'clients/android/app/src'


def test_owner_result_codes_match_go_allowlists():
    native = (ROOT / 'carrier/startupdiag/enabled.go').read_text()
    java = (ANDROID / 'ownerDiagnostic/java/com/familyconnect/app/StartupResult.java').read_text()
    stages = native.split('func stageCode', 1)[1].split('func causeCode', 1)[0]
    causes = native.split('func causeCode', 1)[1].split('func (record', 1)[0]
    allowed_stages = set(re.findall(r'"([A-Z_]+)"', stages))
    allowed_causes = set(re.findall(r'return "([A-Z_]+)"', causes)) | {'NONE'}
    for name, expected in [('STAGES', allowed_stages), ('CAUSES', allowed_causes)]:
        declaration = java.split(name + ' = values(', 1)[1].split(');', 1)[0]
        assert set(re.findall(r'"([A-Z_]+)"', declaration)) == expected


def test_owner_command_keeps_manifest_permission_and_scope():
    namespace = '{http://schemas.android.com/apk/res/android}'
    owner = ET.parse(ANDROID / 'ownerDiagnostic/AndroidManifest.xml')
    receiver = owner.find('.//receiver')
    assert receiver.attrib[namespace + 'permission'] == 'android.permission.DUMP'
    assert receiver.attrib[namespace + 'name'] == '.OwnerFaultReceiver'
    assert 'OwnerFaultReceiver' not in (ANDROID / 'main/AndroidManifest.xml').read_text()
    assert not (ANDROID / 'main/java/com/familyconnect/app/StartupResult.java').exists()
    shim = (ANDROID / 'publicStartup/java/com/familyconnect/app/StartupDiagnostics.java').read_text()
    assert 'owner_startup' not in shim and 'AtomicFile' not in shim and '.initCause' not in shim
    diagnostics = (ANDROID / 'main/java/com/familyconnect/app/Diagnostics.java').read_text()
    assert 'owner-startup' not in diagnostics and 'owner_startup' not in diagnostics


def test_native_completion_and_cancel_do_not_change_legacy_state_order():
    native = (ROOT / 'pilot/android-restricted/native/main.go').read_text()
    assert 'startupdiag.Legacy(err)' in native
    stop = native.split('func fcRestrictedStop', 1)[1]
    assert stop.index('startupdiag.Cancel(owned.ctx)') < stop.index('owned.cancel()') < stop.index('<-owned.done') < stop.index('current = nil')
    assert 'owned.state = 3' in native and 'owned.state = 5' in native and 'owned.state = 1' in native
    java = (ANDROID / 'main/java/com/familyconnect/app/RestrictedTunnelEngine.java').read_text()
    assert java.index('StartupDiagnostics.begin') < java.index('NativeRestricted.state(handle)')
    assert 'StartupDiagnostics.rejected(handle,phase==5?' in java
    assert 'StartupDiagnostics.rejected(handle,ConnectivityOrchestrator.Failure.CANCELLED)' in java


def test_original_red_regression_expectation_is_unchanged():
    source = (ROOT / 'carrier/bootstrap/localize_primary_error_test.go').read_text()
    assert 'if !errors.Is(actual, primary)' in source
    assert 'primary := context.DeadlineExceeded' in source
    assert 'test.Fatalf' in source
