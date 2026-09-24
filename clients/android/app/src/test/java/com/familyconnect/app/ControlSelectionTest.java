package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlSelectionTest {
    static byte[] load(String name)throws Exception {
        try(var in=ControlSelectionTest.class.getClassLoader().getResourceAsStream("control-selection-v1/"+name)) {
            assertNotNull(in);return in.readAllBytes();
        }
    }
    static final class Harness implements AutoCloseable {
        final ControlTransactionTest.Memory store=new ControlTransactionTest.Memory();
        final ControlApplicationTest.Host host=new ControlApplicationTest.Host();
        final ControlIdentity identity;final byte[] anchor;long now=1000;
        ControlJournal journal;ControlTransaction core;
        Harness()throws Exception {
            var f=ControlJson.parse(load("TEST-ONLY-identity.json")).getAsJsonObject();
            byte[] secret=new byte[96];
            System.arraycopy(ControlProtocol.base64(f.get("rns_private_b64").getAsString(),true),0,secret,0,64);
            System.arraycopy(ControlProtocol.base64(f.get("wg_private_b64").getAsString(),true),0,secret,64,32);
            identity=ControlIdentity.restore(secret);Arrays.fill(secret,(byte)0);
            anchor=ControlProtocol.base64(f.get("anchor_b64").getAsString(),true);
            restart();journal.initialize();assertEquals("COMMITTED",core.receive(load("two-gateways.envelope")));
        }
        void restart(){journal=new ControlJournal(store,identity,anchor,"0.2.13",true);core=new ControlTransaction(journal,new ControlApplication(host,identity,()->"dynamic-node-47"),()->now);}
        public void close(){identity.close();}
    }
    @Test public void fixtureIntegrity()throws Exception {
        byte[] raw=load("manifest.json");assertEquals("5143507c95346f828f3252f412fc2b9ab754e6ad0da9044b344f0d17065eaf8c",ControlProtocol.hash(raw));
        var m=ControlJson.parse(raw).getAsJsonObject();assertTrue(m.get("test_only").getAsBoolean());
        for(var entry:m.getAsJsonObject("files").entrySet()) {
            byte[] bytes=load(entry.getKey());var v=entry.getValue().getAsJsonObject();
            assertEquals(v.get("size").getAsInt(),bytes.length);assertEquals(v.get("sha256").getAsString(),ControlProtocol.hash(bytes));
        }
    }
    @Test public void switchPersistsWithoutRevisionAckOrReplayChanges()throws Exception {
        try(var h=new Harness()) {
            var before=h.journal.read();
            assertEquals("SELECTED",h.core.selectGateway("second-node"));
            var after=h.journal.read();assertEquals(2,after.get("schema").getAsInt());
            for(String field:new String[]{"floor","result","outbox"})assertEquals(before.get(field),after.get(field));
            assertEquals(before.getAsJsonObject("committed").get("digest"),after.getAsJsonObject("committed").get("digest"));
            assertTrue(h.host.profiles.get("awg").getAsString().contains("198.51.100.2:51820"));
            int writes=h.host.saves;assertEquals("SELECTED",h.core.selectGateway("second-node"));assertEquals(writes,h.host.saves);
            h.restart();assertEquals("IDLE",h.core.recover());
            assertEquals("COMMITTED",h.core.receive(load("two-gateways.envelope")));assertEquals(writes,h.host.saves);
            h.host.stop();assertEquals("RESUMED",h.core.resume());assertEquals(writes,h.host.saves);
            assertEquals("COMMITTED",h.core.receive(load("next.envelope")));
            assertTrue(h.journal.read().get("selected_gateway").isJsonNull());
            assertEquals(2,h.journal.read().get("floor").getAsInt());
        }
    }
    @Test public void unknownExpiredClockAndOwnerRefuseWithoutWrites()throws Exception {
        try(var h=new Harness()) {
            byte[] original=h.store.raw.clone();int saves=h.host.saves;
            assertThrows(IOException.class,()->h.core.selectGateway("missing"));
            h.now=2000;assertThrows(ControlProtocol.Rejected.class,()->h.core.selectGateway("second-node"));
            h.now=999;assertThrows(ControlProtocol.Rejected.class,()->h.core.selectGateway("second-node"));
            h.now=1000;Object owner=new Object();ControlOperations.APP.claim(owner);
            try{assertThrows(IOException.class,()->h.core.selectGateway("second-node"));}finally{ControlOperations.APP.release(owner);}
            assertArrayEquals(original,h.store.raw);assertEquals(saves,h.host.saves);
        }
    }
    @Test public void healthAndPartialSaveRollbackPreserveOldSelection()throws Exception {
        for(boolean partial:new boolean[]{false,true})try(var h=new Harness()) {
            assertEquals("SELECTED",h.core.selectGateway("dynamic-node-47"));
            var original=h.host.profiles.deepCopy();var outbox=h.journal.read().get("outbox").deepCopy();
            h.host.good=partial;h.host.failSave=partial;
            assertEquals("ROLLED_BACK",h.core.selectGateway("second-node"));
            assertEquals(original,h.host.profiles);assertEquals("awg",h.host.active);
            assertEquals("dynamic-node-47",h.journal.read().get("selected_gateway").getAsString());
            assertEquals(outbox,h.journal.read().get("outbox"));
        }
    }
    @Test public void crashesBeforeAndAfterEachSelectionWriteRecover()throws Exception {
        for(int boundary=1;boundary<=2;boundary++)for(boolean after:new boolean[]{false,true})try(var h=new Harness()) {
            var original=h.host.profiles.deepCopy();h.store.failAt=h.store.writes+boundary;h.store.after=after;
            assertThrows(ControlTransactionTest.Death.class,()->h.core.selectGateway("second-node"));
            h.store.failAt=-1;h.restart();String result=h.core.recover();
            if(boundary==2&&after) {
                assertEquals("IDLE",result);assertEquals("second-node",h.journal.read().get("selected_gateway").getAsString());
                assertTrue(h.host.profiles.get("awg").getAsString().contains("198.51.100.2:51820"));
            }else {
                assertEquals(boundary==1&&!after?"IDLE":"ROLLED_BACK",result);assertEquals(original,h.host.profiles);
            }
            assertEquals(1,h.journal.read().get("floor").getAsInt());
        }
    }
    @Test public void expiredPendingSwitchNeverReconnectsBaseline()throws Exception {
        try(var h=new Harness()) {
            h.store.failAt=h.store.writes+2;
            assertThrows(ControlTransactionTest.Death.class,()->h.core.selectGateway("second-node"));
            h.store.failAt=-1;h.now=2000;h.restart();assertEquals("ROLLED_BACK",h.core.recover());assertNull(h.host.active);
        }
    }
    @Test public void failedRollbackBlocksNewSelectionUntilRecovery()throws Exception {
        try(var h=new Harness()) {
            h.host.failStop=true;
            assertEquals("FAILED",h.core.selectGateway("second-node"));
            assertEquals("SWITCHING",h.journal.read().get("phase").getAsString());
            assertThrows(IOException.class,()->h.core.selectGateway("dynamic-node-47"));
            h.host.failStop=false;h.restart();assertEquals("ROLLED_BACK",h.core.recover());
            assertEquals("SELECTED",h.core.selectGateway("second-node"));
        }
    }
    @Test public void expiryDuringHealthCannotCommitOrReconnect()throws Exception {
        try(var h=new Harness()) {
            int[] reads={0};
            var core=new ControlTransaction(h.journal,new ControlApplication(h.host,h.identity,()->"dynamic-node-47"),()->++reads[0]==1?1000:2000);
            assertEquals("ROLLED_BACK",core.selectGateway("second-node"));assertNull(h.host.active);
            assertTrue(h.journal.read().get("selected_gateway").isJsonNull());
        }
    }
    @Test public void invalidPersistedSelectionIsRejected()throws Exception {
        try(var h=new Harness()) {
            assertEquals("SELECTED",h.core.selectGateway("second-node"));
            var valid=h.journal.read();
            for(String field:new String[]{"selected_gateway","pending_gateway"}) {
                var bad=valid.deepCopy();bad.addProperty(field,"missing");
                assertThrows(Exception.class,()->h.journal.save(bad));
            }
        }
    }
}
