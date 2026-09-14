package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlApplicationTest {
    static final class Host implements ControlApplication.Host {
        JsonObject profiles=new JsonObject();String active="wg";long lease;
        int stops,starts,saves;boolean good=true,cancelled,cancelOnHealth,failSave,failStop;
        Host(){profiles.addProperty("wg","manual-wg");profiles.addProperty("awg","manual-awg");profiles.add("tcp",JsonNull.INSTANCE);}
        public JsonObject capture(){JsonObject r=new JsonObject();r.addProperty("schema",1);r.add("profiles",profiles.deepCopy());r.addProperty("active",active);r.addProperty("lease",lease);return r;}
        public void validate(String slot,String raw)throws Exception{if(raw.isEmpty()||raw.contains("LOCAL_DEVICE_KEY"))throw new IOException("Invalid local profile");}
        public void stop()throws Exception{stops++;if(failStop)throw new IOException("Shutdown pending");active=null;lease=0;}
        public void save(String slot,String profile)throws Exception{profiles.addProperty(slot,profile);saves++;if(failSave){failSave=false;throw new IOException("Partial write");}}
        public void start(String slot,long expiry){starts++;active=slot;lease=expiry;}
        public boolean healthy(){if(cancelOnHealth)cancelled=true;return good;}
        public boolean cancelled(){return cancelled;}
    }
    static ControlTransaction core(ControlTransactionTest.Harness h,Host host){return new ControlTransaction(h.journal,new ControlApplication(host,h.identity),()->h.clock[0]);}
    @Test public void commitBindsLocalKeyAndPreservesOtherSlots()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();ControlTransaction core=core(h,host);
            assertEquals("COMMITTED",core.receive(ControlTransactionTest.resource("valid-wg.envelope")));
            String wg=host.profiles.get("wg").getAsString();byte[] privateKey=h.identity.wireguardPrivateKey();
            try{assertTrue(wg.contains(Base64.getEncoder().encodeToString(privateKey)));}finally{Arrays.fill(privateKey,(byte)0);}
            assertFalse(wg.contains("LOCAL_DEVICE_KEY"));assertEquals("manual-awg",host.profiles.get("awg").getAsString());
            assertTrue(host.profiles.get("tcp").isJsonNull());assertEquals(1,host.starts);assertEquals(4600,host.lease);
            assertEquals("COMMITTED",core.receive(ControlTransactionTest.resource("valid-wg.envelope")));assertEquals(1,host.starts);
        }
    }
    @Test public void partialWriteRestoresAllProfilesAndBaselineConnection()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();JsonObject original=host.profiles.deepCopy();host.failSave=true;
            assertEquals("ROLLED_BACK",core(h,host).receive(ControlTransactionTest.resource("valid-wg.envelope")));
            assertEquals(original,host.profiles);assertEquals("wg",host.active);assertEquals(1,host.starts);assertEquals(1,h.state().get("floor").getAsLong());
        }
    }
    @Test public void cancellationRestoresFilesWithoutReconnect()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();JsonObject original=host.profiles.deepCopy();host.cancelOnHealth=true;
            assertEquals("ROLLED_BACK",core(h,host).receive(ControlTransactionTest.resource("valid-wg.envelope")));
            assertEquals(original,host.profiles);assertNull(host.active);assertEquals(1,host.starts);
        }
    }
    @Test public void failedHealthRestoresPreviousConnection()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();host.good=false;JsonObject original=host.profiles.deepCopy();
            assertEquals("ROLLED_BACK",core(h,host).receive(ControlTransactionTest.resource("valid-wg.envelope")));
            assertEquals(original,host.profiles);assertEquals("wg",host.active);assertEquals(2,host.starts);
        }
    }
    @Test public void crashBeforeCommitRestoresDurableSnapshot()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();JsonObject original=host.profiles.deepCopy();h.store.failAt=4;
            assertThrows(ControlTransactionTest.Death.class,()->core(h,host).receive(ControlTransactionTest.resource("valid-wg.envelope")));
            h.store.failAt=-1;h.restart();assertEquals("ROLLED_BACK",core(h,host).recover());
            assertEquals(original,host.profiles);assertEquals("wg",host.active);assertEquals(1,h.state().get("floor").getAsLong());
        }
    }
    @Test public void expiredPreviousIsRestoredOnDiskButNeverReconnected()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();ControlTransaction core=core(h,host);
            assertEquals("COMMITTED",core.receive(ControlTransactionTest.resource("valid-wg.envelope")));
            JsonObject good=host.profiles.deepCopy();h.store.failAt=h.store.writes+3;h.store.after=true;
            assertThrows(ControlTransactionTest.Death.class,()->core.receive(ControlTransactionTest.resource("valid-next.envelope")));
            h.store.failAt=-1;h.clock[0]=4600;h.restart();
            assertEquals("ROLLED_BACK",core(h,host).recover());assertEquals(good,host.profiles);assertNull(host.active);assertEquals(2,host.starts);
        }
    }
    @Test public void corruptSnapshotStopsCandidateWithoutWritingUntrustedSlots()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();ControlApplication app=new ControlApplication(host,h.identity);
            var v=h.journal.verify(ControlTransactionTest.resource("valid-wg.envelope"),1000);JsonObject bad=host.capture();
            bad.getAsJsonObject("profiles").addProperty("../../profile", "unsafe");
            assertThrows(Exception.class,()->app.rollback(v,null,bad,true));assertEquals(1,host.stops);assertEquals(0,host.saves);assertNull(host.active);
        }
    }
    @Test public void multipleProfilesForOneSlotAreRefusedBeforeStop()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();ControlApplication app=new ControlApplication(host,h.identity);
            var v=h.journal.verify(ControlTransactionTest.resource("valid-wg.envelope"),1000);JsonObject state=v.state();
            JsonObject second=state.getAsJsonArray("transport_profiles").get(0).getAsJsonObject().deepCopy();second.addProperty("profile_id","second");state.getAsJsonArray("transport_profiles").add(second);
            ControlProfiles.validate(state);var two=new ControlProtocol.Verified(state,v.digest);
            assertThrows(IOException.class,()->app.apply(two,host.capture()));assertEquals(0,host.stops);assertEquals(0,host.saves);
        }
    }
    @Test public void matchingServiceOwnerCanApplyButForeignAndStaleOwnersCannot()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();Object owner=new Object();ControlOperations.APP.claim(owner);
            try{
                var foreign=new ControlTransaction(h.journal,new ControlApplication(host,h.identity),()->h.clock[0],new Object());
                assertThrows(ControlOperations.Stale.class,foreign::recover);
                var owned=new ControlTransaction(h.journal,new ControlApplication(host,h.identity),()->h.clock[0],owner);
                assertEquals("COMMITTED",owned.receive(ControlTransactionTest.resource("valid-wg.envelope")));
            }finally{ControlOperations.APP.release(owner);}
            var stale=new ControlTransaction(h.journal,new ControlApplication(host,h.identity),()->h.clock[0],owner);
            assertThrows(ControlOperations.Stale.class,stale::recover);
        }
    }
    @Test public void failedStopPreventsAnyProfileRewrite()throws Exception{
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();host.failStop=true;
            assertEquals("FAILED",core(h,host).receive(ControlTransactionTest.resource("valid-wg.envelope")));
            assertEquals(0,host.saves);assertEquals("ROLLING_BACK",h.state().get("phase").getAsString());
            host.failStop=false;assertEquals("ROLLED_BACK",core(h,host).recover());
        }
    }
}
