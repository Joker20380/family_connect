package com.familyconnect.app;

import android.content.Context;
import android.util.AtomicFile;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.google.gson.*;
import java.io.File;
import java.security.KeyStore;
import java.util.Arrays;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Real Android encrypted journal; simulated VPN host. Empty debug pilot only. */
@RunWith(AndroidJUnit4.class)
public class ControlSelectionRuntimeTest {
    private static final String ALIAS="family-connect-control-journal-v1";
    private byte[] load(String name)throws Exception {
        try(var in=InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("control-selection-v1/"+name)) {
            return in.readAllBytes();
        }
    }
    private static final class Host implements ControlApplication.Host {
        JsonObject profiles=new JsonObject();String active;long lease;boolean good=true;
        Host(){for(String slot:new String[]{"wg","awg","tcp"})profiles.add(slot,JsonNull.INSTANCE);}
        public JsonObject capture(){var r=new JsonObject();r.addProperty("schema",1);r.add("profiles",profiles.deepCopy());r.addProperty("active",active);r.addProperty("lease",lease);return r;}
        public void validate(String slot,String raw){assertFalse(raw.isEmpty());assertFalse(raw.contains("LOCAL_DEVICE_KEY"));}
        public void stop(){active=null;lease=0;}
        public void save(String slot,String raw){profiles.addProperty(slot,raw);}
        public void start(String slot,long expiry){active=slot;lease=expiry;}
        public boolean healthy(){return good;}
        public boolean cancelled(){return false;}
    }
    @Test public void selectionReopensAndRollsBackInEncryptedJournal()throws Exception {
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertEquals("com.familyconnect.app.pilot",context.getPackageName());
        assertTrue((context.getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0);
        assertEquals("true",InstrumentationRegistry.getArguments().getString("fc_disposable"));
        ControlOperations.APP.requireIdle();assertEquals("off",ConnectionService.status);
        for(Transport t:Transport.values())assertFalse(new ProfileStore(context,t).present());
        KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
        // All preconditions are outside cleanup: never delete pre-existing user state.
        for(String name:new String[]{"identity","journal","enrollment"}) {
            assertFalse(keys.containsAlias("family-connect-control-"+name+"-v1"));
            for(String suffix:new String[]{"",".bak",".new"})
                assertFalse(new File(context.getNoBackupFilesDir(),"control-"+name+".enc"+suffix).exists());
        }
        var manifest=load("manifest.json");
        assertEquals("5143507c95346f828f3252f412fc2b9ab754e6ad0da9044b344f0d17065eaf8c",ControlProtocol.hash(manifest));
        for(var entry:ControlJson.parse(manifest).getAsJsonObject().getAsJsonObject("files").entrySet()) {
            byte[] raw=load(entry.getKey());var item=entry.getValue().getAsJsonObject();
            assertEquals(item.get("size").getAsInt(),raw.length);assertEquals(item.get("sha256").getAsString(),ControlProtocol.hash(raw));
        }
        var fixture=ControlJson.parse(load("TEST-ONLY-identity.json")).getAsJsonObject();
        byte[] secret=new byte[96];
        System.arraycopy(ControlProtocol.base64(fixture.get("rns_private_b64").getAsString(),true),0,secret,0,64);
        System.arraycopy(ControlProtocol.base64(fixture.get("wg_private_b64").getAsString(),true),0,secret,64,32);
        try(ControlIdentity identity=ControlIdentity.restore(secret)) {
            Arrays.fill(secret,(byte)0);
            byte[] anchor=ControlProtocol.base64(fixture.get("anchor_b64").getAsString(),true);
            Host host=new Host();
            var journal=new ControlJournal(new ControlJournalVault(context),identity,anchor,"0.2.13",true);
            journal.initialize();assertNull(keys.getKey(ALIAS,null).getEncoded());
            var core=new ControlTransaction(journal,new ControlApplication(host,identity,()->"dynamic-node-47"),()->1000);
            assertEquals("COMMITTED",core.receive(load("two-gateways.envelope")));
            var before=journal.read();assertEquals("SELECTED",core.selectGateway("second-node"));
            var reopened=new ControlJournal(new ControlJournalVault(context),identity,anchor,"0.2.13",true);
            core=new ControlTransaction(reopened,new ControlApplication(host,identity,()->"dynamic-node-47"),()->1000);
            assertEquals("IDLE",core.recover());host.stop();assertEquals("RESUMED",core.resume());
            assertTrue(host.profiles.get("awg").getAsString().contains("198.51.100.2:51820"));
            host.good=false;assertEquals("ROLLED_BACK",core.selectGateway("dynamic-node-47"));
            var after=reopened.read();assertEquals("second-node",after.get("selected_gateway").getAsString());
            assertEquals("IDLE",after.get("phase").getAsString());
            for(String field:new String[]{"floor","outbox","result"})assertEquals(before.get(field),after.get(field));
            assertEquals(before.getAsJsonObject("committed").get("digest"),after.getAsJsonObject("committed").get("digest"));
        } finally {
            Arrays.fill(secret,(byte)0);
            new AtomicFile(new File(context.getNoBackupFilesDir(),"control-journal.enc")).delete();
            keys.deleteEntry(ALIAS);
        }
    }
}
