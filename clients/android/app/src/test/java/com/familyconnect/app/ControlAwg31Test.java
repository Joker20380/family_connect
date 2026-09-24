package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlAwg31Test {
    @Test public void journalAppliesRestartsAndRollsBackProtectedProfile()throws Exception {
        var f=ControlJson.parse(load("TEST-ONLY-identity.json")).getAsJsonObject();
        byte[] material=new byte[96];
        System.arraycopy(ControlProtocol.base64(f.get("rns_private_b64").getAsString(),true),0,material,0,64);
        System.arraycopy(ControlProtocol.base64(f.get("wg_private_b64").getAsString(),true),0,material,64,32);
        try(var identity=ControlIdentity.restore(material)) {
            java.util.Arrays.fill(material,(byte)0);
            byte[] anchor=ControlProtocol.base64(f.get("anchor_b64").getAsString(),true),raw=load("valid.envelope");
            for(boolean healthy:new boolean[]{true,false}) {
                var store=new ControlTransactionTest.Memory();
                var journal=new ControlJournal(store,identity,anchor,"0.2.13",true);journal.initialize();
                var host=new ControlApplicationTest.Host();host.good=healthy;
                var baseline=host.profiles.deepCopy();
                var app=new ControlApplication(host,identity,()->"dynamic-node-47");
                var core=new ControlTransaction(journal,app,()->1000);
                String expected=healthy?"COMMITTED":"ROLLED_BACK";
                assertEquals(expected,core.receive(raw));
                if(healthy) {
                    String local=host.profiles.get("awg").getAsString();
                    assertFalse(local.contains("LOCAL_DEVICE_KEY"));
                    assertTrue(ProfileValidator.validate(local,Transport.AWG).contains("RandomTrailers = true"));
                    assertEquals("awg",host.active);
                }else {assertEquals(baseline,host.profiles);assertEquals("wg",host.active);}
                int starts=host.starts;
                var reopened=new ControlJournal(store,identity,anchor,"0.2.13",true);
                var restarted=new ControlTransaction(reopened,new ControlApplication(host,identity,()->"dynamic-node-47"),()->1000);
                assertEquals("IDLE",restarted.recover());assertEquals(expected,restarted.receive(raw));assertEquals(starts,host.starts);
                assertEquals(1,reopened.read().get("floor").getAsLong());
                if(healthy)assertThrows(ControlProtocol.Rejected.class,()->new ControlJournal(store,identity,anchor,"0.2.13").read());
            }
        }finally{java.util.Arrays.fill(material,(byte)0);}
    }
    private byte[] load(String name)throws Exception {
        try(var stream=getClass().getClassLoader().getResourceAsStream("control-awg31-v1/"+name)) {
            assertNotNull(stream);return stream.readAllBytes();
        }
    }
    @Test public void sharedCorpusWithExplicitCapability()throws Exception {
        byte[] raw=load("manifest.json");
        assertEquals("51a0e53434e46876212a09945762a970c2943020220250f219042b12c71f7039",ControlProtocol.hash(raw));
        JsonObject manifest=ControlJson.parse(raw).getAsJsonObject();
        assertTrue(manifest.get("test_only").getAsBoolean());
        for(var entry:manifest.getAsJsonObject("files").entrySet()) {
            byte[] bytes=load(entry.getKey());var metadata=entry.getValue().getAsJsonObject();
            assertEquals(metadata.get("size").getAsInt(),bytes.length);
            assertEquals(metadata.get("sha256").getAsString(),ControlProtocol.hash(bytes));
        }
        var f=ControlJson.parse(load("TEST-ONLY-identity.json")).getAsJsonObject();
        byte[] anchor=ControlProtocol.base64(f.get("anchor_b64").getAsString(),true);
        byte[] privateKey=ControlProtocol.base64(f.get("rns_private_b64").getAsString(),true);
        byte[] publicKey=ControlProtocol.base64(f.get("public_identity_b64").getAsString(),true);
        for(var item:manifest.getAsJsonArray("configurations"))for(boolean supported:new boolean[]{false,true}) {
            var v=item.getAsJsonObject();String category;ControlProtocol.Verified verified=null;
            try {
                verified=ControlProtocol.verifyConfiguration(load(v.get("input").getAsString()),anchor,privateKey,publicKey,
                    f.get("wireguard_public_key").getAsString(),v.get("client_version").getAsString(),v.get("now").getAsLong(),supported);
                category="ACCEPT";
            }catch(ControlProtocol.Rejected e){category=e.category;}
            assertEquals(v.get("id").getAsString()+" capability="+supported,v.get(supported?"expected":"legacy_expected").getAsString(),category);
            if(verified!=null) {
                assertEquals(v.get("payload"),verified.state());
                String config=verified.state().getAsJsonArray("transport_profiles").get(0).getAsJsonObject().get("config").getAsString();
                // The native import parser must preserve the protection settings too.
                String local=config.replace("LOCAL_DEVICE_KEY",f.get("wg_private_b64").getAsString());
                String normalized=ProfileValidator.validate(local,Transport.AWG);
                for(String line:local.split("\n"))if(line.contains(" = "))assertTrue(normalized.contains(line));
                refusals(verified.state(),config);
            }
        }
    }
    private void refusals(JsonObject original,String config)throws Exception {
        String[] bad={config.replace("DisableCookies = false\n",""),
            config.replace("RandomTrailers = true","RandomTrailers = yes"),
            config.replace("DisableCookies = false","DisableCookies = 0"),
            config.replace("H1 = 1\n","H1 = 5\n"),config.replace("S1 = 32","S1 = 11"),
            config.replace("S1 = 32","S1 = 48"),config.replace("0-64","257"),
            config.replace("0-64","64-0"),config.replace("[Peer]","PostUp = command\n[Peer]"),
            config.replaceAll("HeaderProtectionKey = [^\\n]+","HeaderProtectionKey = "+java.util.Base64.getEncoder().encodeToString(new byte[32]))};
        for(String invalid:bad) {
            JsonObject changed=original.deepCopy();changed.getAsJsonArray("transport_profiles").get(0).getAsJsonObject().addProperty("config",invalid);
            assertThrows(Exception.class,()->ControlProfiles.validate(changed));
        }
    }
}
