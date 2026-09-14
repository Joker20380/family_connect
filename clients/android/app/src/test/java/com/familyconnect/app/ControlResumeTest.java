package com.familyconnect.app;

import java.io.IOException;
import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlResumeTest {
    static class Host implements ControlApplication.Host {
        long[] clock;long healthTime;boolean die;
        JsonObject profiles=new JsonObject();String active="wg";long lease;
        int stops,starts,saves;boolean good=true,cancelled,cancelOnHealth,failSave,failStop;
        Host(){profiles.addProperty("wg","manual-wg");profiles.addProperty("awg","manual-awg");profiles.add("tcp",JsonNull.INSTANCE);}
        public JsonObject capture(){JsonObject r=new JsonObject();r.addProperty("schema",1);r.add("profiles",profiles.deepCopy());r.addProperty("active",active);r.addProperty("lease",lease);return r;}
        public void validate(String slot,String raw)throws Exception{if(raw.isEmpty()||raw.contains("LOCAL_DEVICE_KEY"))throw new IOException("Invalid local profile");}
        public void stop()throws Exception{stops++;if(failStop)throw new IOException("Shutdown pending");active=null;lease=0;}
        public void save(String slot,String profile)throws Exception{profiles.addProperty(slot,profile);saves++;if(failSave){failSave=false;throw new IOException("Partial write");}}
        public void start(String slot,long expiry){starts++;active=slot;lease=expiry;}
        public boolean healthy(){if(healthTime!=0)clock[0]=healthTime;if(die)throw new ControlTransactionTest.Death();if(cancelOnHealth)cancelled=true;return good;}
        public boolean cancelled(){return cancelled;}
    }
    static ControlTransaction core(ControlTransactionTest.Harness h,Host host){return new ControlTransaction(h.journal,new ControlApplication(host,h.identity),()->h.clock[0]);}
    static void committed(ControlTransactionTest.Harness h,Host host)throws Exception {
        host.clock=h.clock;assertEquals("COMMITTED",core(h,host).receive(ControlTransactionTest.resource("valid-wg.envelope")));
        host.stop();h.restart();
    }
    @Test public void reconnectVerifiesWithoutWritingProfilesOrChangingProtocolState()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);var before=h.state();var profiles=host.profiles.deepCopy();int saves=host.saves;
            h.clock[0]=1001;assertEquals("RESUMED",core(h,host).resume());
            assertEquals("wg",host.active);assertEquals(4600,host.lease);assertEquals(saves,host.saves);assertEquals(profiles,host.profiles);
            for(String key:new String[]{"floor","committed","staged","baseline","result","outbox","phase"})assertEquals(key,before.get(key),h.state().get(key));
            assertEquals(1001,h.state().get("last_now").getAsLong());
        }
    }
    @Test public void emptyJournalDoesNotActivate()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();host.stop();assertEquals("IDLE",core(h,host).resume());assertEquals(0,host.starts);
        }
    }
    @Test public void expiredAndRegressedClocksCannotStart()throws Exception {
        for(long now:new long[]{4600,999})try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);h.clock[0]=now;
            assertThrows(ControlProtocol.Rejected.class,()->core(h,host).resume());assertNull(host.active);assertEquals(1,host.starts);
        }
    }
    @Test public void modifiedOrMissingSignedSlotIsNotSilentlyRepaired()throws Exception {
        for(String profile:new String[]{"modified",null})try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);host.profiles.addProperty("wg",profile);int saves=host.saves;
            assertThrows(IOException.class,()->core(h,host).resume());assertNull(host.active);assertEquals(1,host.starts);assertEquals(saves,host.saves);
        }
    }
    @Test public void healthFailureCancellationAndLeaseExpiryStopResumedEngine()throws Exception {
        for(int scenario=0;scenario<4;scenario++)try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);var previous=h.state();
            if(scenario==0)host.good=false;if(scenario==1)host.cancelOnHealth=true;if(scenario==2)host.healthTime=4600;if(scenario==3)host.healthTime=999;
            assertThrows(Exception.class,()->core(h,host).resume());assertNull(host.active);assertEquals(2,host.starts);
            assertEquals(previous.get("committed"),h.state().get("committed"));assertEquals(previous.get("outbox"),h.state().get("outbox"));
        }
    }
    @Test public void revokedPermissionDoesNotStart()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);host.cancelled=true;
            assertThrows(IOException.class,()->core(h,host).resume());assertNull(host.active);assertEquals(1,host.starts);
        }
    }
    @Test public void pendingApplyMustRecoverBeforeResume()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);h.store.failAt=h.store.writes+2;h.store.after=true;
            assertThrows(ControlTransactionTest.Death.class,()->core(h,host).receive(ControlTransactionTest.resource("valid-next.envelope")));
            h.store.failAt=-1;assertThrows(IOException.class,()->core(h,host).resume());assertEquals(1,host.starts);
            assertEquals("ROLLED_BACK",core(h,host).recover());
        }
    }
    @Test public void corruptEnvelopeAndWrongTrustCannotResume()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);var good=h.state();var bad=good.deepCopy();
            bad.getAsJsonObject("committed").addProperty("digest","0".repeat(64));h.store.raw=ControlJournal.encode(bad);
            assertThrows(Exception.class,()->core(h,host).resume());assertEquals(1,host.starts);
            h.store.raw=ControlJournal.encode(good);h.journal=new ControlJournal(h.store,h.identity,new byte[32],"0.2.9");
            assertThrows(Exception.class,()->core(h,host).resume());assertEquals(1,host.starts);
        }
    }
    @Test public void writeFailureBeforeStartAndAfterHealthRemainRetryable()throws Exception {
        for(int boundary:new int[]{1,2})try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);var committed=h.state().get("committed").deepCopy();
            var storage=new ControlJournal.Storage(){int writes;
                public byte[] read()throws Exception{return h.store.read();}
                public void create(byte[] raw)throws Exception{h.store.create(raw);}
                public void write(byte[] raw)throws Exception{if(++writes==boundary)throw new IOException("disk");h.store.write(raw);}
            };
            h.journal=new ControlJournal(storage,h.identity,h.anchor,"0.2.9");
            assertThrows(IOException.class,()->core(h,host).resume());assertNull(host.active);assertEquals(boundary,host.starts);
            h.restart();assertEquals(committed,h.state().get("committed"));assertEquals("RESUMED",core(h,host).resume());
        }
    }
    @Test public void processDeathDuringHealthHasNoPartialProfileTransaction()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);var before=h.state();var profiles=host.profiles.deepCopy();host.die=true;
            assertThrows(ControlTransactionTest.Death.class,()->core(h,host).resume());
            // Simulated OS engine destruction; real Android process-death acceptance remains separate.
            host.stop();host.die=false;h.restart();
            assertEquals(before,h.state());assertEquals(profiles,host.profiles);assertEquals("IDLE",core(h,host).recover());
            assertEquals("RESUMED",core(h,host).resume());
        }
    }
    @Test public void foreignServiceCannotResume()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Host host=new Host();committed(h,host);Object owner=new Object();ControlOperations.APP.claim(owner);
            try{
                assertThrows(IOException.class,()->core(h,host).resume());
                var stale=new ControlTransaction(h.journal,new ControlApplication(host,h.identity),()->h.clock[0],new Object());
                assertThrows(ControlOperations.Stale.class,stale::resume);assertEquals(1,host.starts);
            }finally{ControlOperations.APP.release(owner);}
        }
    }
}
