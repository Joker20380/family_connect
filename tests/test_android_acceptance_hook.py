from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'clients/android/app'
ANDROID = '{http://schemas.android.com/apk/res/android}'


def test_public_manifest_does_not_export_private_control():
    manifest = ET.parse(APP / 'src/main/AndroidManifest.xml')
    activities = [item.attrib[ANDROID + 'name'] for item in manifest.findall('.//activity')]
    assert '${launcherActivity}' in activities
    assert not any('Diagnostic' in name for name in activities)
    build = (APP / 'build.gradle').read_text()
    assert "launcherActivity: 'com.familyconnect.app.FriendsActivity'" in build
    assert 'debuggable false' in build
    assert "friends.java.srcDir 'src/debug/java'" not in build


def test_private_overlay_is_explicit_and_includes_regressions():
    overlay = (ROOT / 'deploy/friends/restricted/android-canary58-physical.gradle').read_text()
    assert "friends.java.srcDir 'src/debug/java'" in overlay
    assert "testFriends.java.srcDir 'src/testDebug/java'" in overlay
    assert 'versionCode = 58' in overlay


def test_hook_uses_package_launcher_and_durable_override():
    hook = (APP / 'src/debug/java/com/familyconnect/app/OrchestratorDiagnosticActivity.java').read_text()
    assert 'MainActivity.class' not in hook
    assert 'FriendsActivity.class' not in hook
    assert 'getLaunchIntentForPackage(getPackageName())' in hook
    assert 'if(!committed)throw new IllegalStateException()' in hook
    assert 'LAUNCHER_UNAVAILABLE' in hook
    assert 'acceptance_override' in hook
    assert 'output.getFD().sync()' in hook


def test_normal_override_off_remains_default_and_debug_only():
    automatic = (APP / 'src/main/java/com/familyconnect/app/AutomaticConnection.java').read_text()
    assert 'if(debug&&context.getSharedPreferences("orchestrator-diagnostic",Context.MODE_PRIVATE).getBoolean("deny_"+id,false))' in automatic
    assert 'ApplicationInfo.FLAG_DEBUGGABLE' in automatic
