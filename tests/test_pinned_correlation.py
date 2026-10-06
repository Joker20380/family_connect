from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_correlation_build_tag_and_public_isolation():
    source = ROOT / 'carrier/sessiontrace'
    for name in ['correlation.go', 'correlation_command.go', 'correlation_linux.go']:
        assert (source / name).read_text().startswith('//go:build fc_owner_diagnostic')
    disabled = (source / 'correlation_disabled.go').read_text()
    assert 'return false' in disabled
    assert '{"error":"disabled"}' in disabled
    assert 'net.Listen' not in disabled
    assert 'watches map' not in disabled
    for name in ['trace.go', 'delivery.go']:
        assert 'json:"correlation_watch' not in (source / name).read_text()
        assert 'json:"correlation,omitempty"' not in (source / name).read_text()


def test_correlation_control_auth_and_bounds():
    source = (ROOT / 'carrier/sessiontrace/correlation_linux.go').read_text()
    assert 'SO_PEERCRED' in source and 'credentials.Uid == uint32(os.Geteuid())' in source
    assert 'net.ListenUnix' in source and 'net.Listen(' not in source
    assert 'info.Mode&0777 != 0700' in source
    command = (ROOT / 'carrier/sessiontrace/correlation_command.go').read_text()
    assert '16*1024' in command and 'DisallowUnknownFields' in command
    assert 'decoder.Decode(&trailing) != io.EOF' in command
    implementation = (ROOT / 'carrier/sessiontrace/correlation.go').read_text()
    assert 'const CandidateLimit = 4' in implementation
    assert 'const CorrelationFragments = 8' in implementation
    for forbidden in ['json:"payload', 'json:"destination', 'json:"credential', 'json:"private_key']:
        assert forbidden not in implementation


def test_correlation_android_owner_only():
    android = ROOT / 'clients/android/app/src'
    manifest = android / 'ownerDiagnostic/AndroidManifest.xml'
    assert 'android.permission.DUMP' in manifest.read_text()
    for candidate in android.glob('*/AndroidManifest.xml'):
        if candidate != manifest:
            assert 'OwnerFaultReceiver' not in candidate.read_text()
    receiver = (android / 'ownerDiagnostic/java/com/familyconnect/app/OwnerFaultReceiver.java').read_text()
    assert 'body.length() <= 16384' in receiver
    native = (ROOT / 'pilot/android-restricted/native/fault.go').read_text()
    assert 'trace.CorrelationCommand' in native
    assert '"client"' in native
