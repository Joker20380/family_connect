"""Re-use the pinned100 build recipe with exact100 as parent."""
import os
import subprocess
from prepare import ROOT, BASE, WORK, FIXTURE, patch


def main():
    source=(BASE/'executed-android-build.py').read_text()
    source=source.replace('p1-owner-acceptance-20261021','p1-lifecycle-101-20261021')
    source=source.replace('version_code=100','version_code=101').replace('0.1.18-beta100-lifecycle','0.1.18-beta101-lifecycle')
    source=source.replace('state-client-build/support-cadence99-20261021/android-source','state-client-build/p1-owner-acceptance-20261021/android-source')
    source=source.replace('FamilyConnect-0.1.18-beta99-support.apk','FamilyConnect-0.1.18-beta100-lifecycle.apk')
    target=WORK/'android-source/clients/android/app/src/test/java/com/familyconnect/app/MuxLifecycleTest.java'
    patch(target,'public class MuxLifecycleTest {','''public class MuxLifecycleTest {
    @Test public void incidentHistorySurvivesProjection(){
        JsonObject source=new JsonObject(),raw=new JsonObject();JsonArray incidents=new JsonArray();
        for(int index=0;index<40;index++){
            JsonObject incident=JsonParser.parseString("{\\"class\\":\\"expected\\",\\"detail\\":\\"crossed_reset\\",\\"stream\\":{\\"local_abort\\":true,\\"send_done\\":[0,0,0,0,0,0,123]},\\"payload\\":\\"private\\"}").getAsJsonObject();
            incidents.add(incident);
        }
        raw.add("incidents",incidents);raw.addProperty("expected_crossings",40);raw.addProperty("incident_dropped",8);
        source.add("mux_lifecycle",raw);JsonObject safe=new JsonObject();MuxLifecycle.project(source,safe);
        JsonObject output=safe.getAsJsonObject("mux_lifecycle");
        assertEquals(32,output.getAsJsonArray("incidents").size());assertEquals(40,output.get("expected_crossings").getAsInt());
        assertTrue(output.get("projection_overflow").getAsBoolean());assertFalse(output.toString().contains("private"));
        assertEquals(123,output.getAsJsonArray("incidents").get(0).getAsJsonObject().getAsJsonObject("stream").getAsJsonArray("send_done").get(6).getAsInt());
    }
''')
    runner=WORK/'executed-android-build.py'
    assert not runner.exists()
    subprocess.run(['apply_patch','*** Begin Patch\n*** Add File: '+str(runner)+'\n'+''.join('+'+line+'\n' for line in source.splitlines())+'*** End Patch\n'],check=True)
    os.environ['GIT_DIR']=str(ROOT/'state-client-build/mux-profile-20261020/android-source/.git')
    os.environ['GIT_WORK_TREE']=str(WORK/'android-source')
    exec(compile(source,str(runner),'exec'),dict(__name__='__main__',__file__=str(runner)))


if __name__=='__main__':main()
