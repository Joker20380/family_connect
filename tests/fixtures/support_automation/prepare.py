"""Owner support delta on the exact installed beta97 source, never GitHub main."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/speed_candidate'))
from prepare import write, replace, digest

BASE = ROOT / 'state-client-build/speed-candidate-20261021'
WORK = ROOT / 'state-client-build/support-automation-20261021'
SOURCE = WORK / 'android-source'
JAVA = Path('clients/android/app/src/main/java/com/familyconnect/app')


def frozen_file(relative):
    patch = Path(__file__).with_name('android97-to98.patch').read_text()
    section = patch.split('+++ b/' + str(relative) + '\n', 1)[1].split('\n--- ', 1)[0]
    lines = section.splitlines()
    assert lines[0].startswith('@@ -0,0 ') and all(line.startswith('+') for line in lines[1:])
    return '\n'.join(line[1:] for line in lines[1:]) + '\n'


def integrate(source):
    java = source / JAVA
    path = java / 'Diagnostics.java'
    replace(path, '    static void share(android.app.Activity activity){', '''    static JsonObject supportSnapshot(Context context){
        Diagnostics store=get(context);synchronized(store){store.network();return store.ring.snapshot();}
    }
    static void share(android.app.Activity activity){''')
    path = java / 'FriendsAccessAndroid.java'
    replace(path, 'device/(status|support)', 'device/(status|support|diagnostics)')
    replace(path, '    String supportId() throws Exception {', '''    void supportDiagnostics(JsonObject report)throws Exception{
        deadline=android.os.SystemClock.elapsedRealtime()+15000;
        String raw=report.toString();byte[] encoded=raw.getBytes(StandardCharsets.UTF_8);require(encoded.length<=4096);
        byte[] digest=java.security.MessageDigest.getInstance("SHA-256").digest(encoded);StringBuilder hash=new StringBuilder();
        for(byte value:digest)hash.append(String.format(java.util.Locale.ROOT,"%02x",value&255));
        try(ControlIdentity identity=identity(false)){
            JsonObject request=new JsonObject();request.add("proof",proof(identity,"diagnostics:"+hash,""));request.addProperty("report",raw);
            JsonObject result=post("/friends/device/diagnostics",request);fields(result,"schema report_id stored_at");
            require(integer(result.get("schema"),1)==1&&text(result.get("report_id")).equals(text(report.get("report_id"))));
            integer(result.get("stored_at"),1);
        }
    }
    String supportId() throws Exception {''')
    path = source / 'clients/android/app/src/main/AndroidManifest.xml'
    replace(path, '</application>', '''    <provider android:name=".OwnerSupportProvider" android:authorities="${applicationId}.owner.support"
            android:exported="true" android:permission="android.permission.DUMP" android:grantUriPermissions="false" />
    </application>''')


def main():
    assert not SOURCE.exists(), 'Do not mutate an existing sealed source'
    WORK.mkdir(mode=0o700, parents=True, exist_ok=True)
    assert digest(BASE / 'delivery/FamilyConnect-0.1.18-beta97-speed.apk') == 'd7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f'
    inventory = {str(path.relative_to(BASE/'android-source')):digest(path) for path in (BASE/'android-source').rglob('*') if path.is_file() and not any(part in ('.git','.gradle','build','__pycache__') for part in path.relative_to(BASE/'android-source').parts)}
    write(WORK/'parent-inventory.json',json.dumps(inventory,indent=2,sort_keys=True)+'\n')
    shutil.copytree(BASE/'android-source',SOURCE,ignore=shutil.ignore_patterns('.git','.gradle','build','__pycache__'))
    for name in ('SupportSnapshot.java','SupportAccess.java','SupportAutomation.java','OwnerSupportProvider.java'):
        write(SOURCE/JAVA/name,frozen_file(JAVA/name))
    test=Path('clients/android/app/src/test/java/com/familyconnect/app/SupportSnapshotTest.java')
    write(SOURCE/test,frozen_file(test))
    integrate(SOURCE)
    replace(SOURCE/'clients/android/app/build.gradle',"versionCodeOverride = 97; versionNameOverride = '0.1.18-beta97-speed'","versionCodeOverride = 98; versionNameOverride = '0.1.18-beta98-support'")
    path=SOURCE/JAVA/'FriendsActivity.java'
    replace(path,'        TerminalUi.button(panel,R.string.diagnostics_send,()->Diagnostics.share(this));','        SupportAutomation.controls(this,panel);\n        TerminalUi.button(panel,R.string.diagnostics_send,()->Diagnostics.share(this));')
    replace(path,'@Override protected void onResume(){super.onResume();','@Override protected void onResume(){super.onResume();SupportAutomation.attach(this::supportCommand);')
    replace(path,'@Override protected void onPause(){','@Override protected void onPause(){SupportAutomation.detach();')
    replace(path,'    private void disconnect(){','''    private String supportCommand(String method,String argument){
        if(busy)return "BUSY";
        if("disconnect".equals(method)){reconnect=false;if("off".equals(ConnectionService.status))return "ALREADY_OFF";disconnect();return "DISCONNECT_REQUESTED";}
        if(!"off".equals(ConnectionService.status))return "DISCONNECT_FIRST";
        if("profile".equals(method)){SpeedProfile.save(this,Integer.parseInt(argument.substring(1)));render();return "NEXT_SESSION_"+argument;}
        if(!"telemost".equals(transport))return "SELECT_MESH_IN_APP_FIRST";
        if(VpnService.prepare(this)!=null)return "VPN_PERMISSION_REQUIRED";
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)return "NOTIFICATION_PERMISSION_REQUIRED";
        prepareConnect();return "CONNECT_REQUESTED";
    }
    private void disconnect(){''')
    path=SOURCE/JAVA/'Diagnostics.java'
    replace(path,'            store.save(false);\n        }}catch(Exception ignored){}','            store.save(false);\n        }SupportAutomation.tick(context);}catch(Exception ignored){}')
    path=SOURCE/JAVA/'DiagnosticRing.java'
    marker='        SpeedReceipt.project(source,safe);'
    replace(path,marker,marker+'\n        JsonObject reasons=SupportSnapshot.object(source,"protocol_error_reasons"),safeReasons=new JsonObject();\n        for(String reason:SupportSnapshot.REASONS)SupportSnapshot.number(reasons,safeReasons,reason);\n        if(safeReasons.size()>0)safe.add("protocol_error_reasons",safeReasons);')
    print('PREPARED_EXACT97_SUPPORT98_SOURCE_NOT_INSTALLED')


if __name__=='__main__':
    main()
