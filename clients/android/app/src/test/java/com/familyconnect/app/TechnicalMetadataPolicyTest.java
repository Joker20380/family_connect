package com.familyconnect.app;

import java.util.HashMap;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;

public class TechnicalMetadataPolicyTest {
    static final class Store implements TechnicalMetadataPolicy.Store {
        Map<String,Object> values=new HashMap<>();boolean fail;
        public Map<String,Object> read(){return new HashMap<>(values);}
        public boolean commit(Map<String,Object> next){if(fail)return false;values=new HashMap<>(next);return true;}
    }
    @Test public void freshInitializationIsDurableBeforeAnyCollectionAndNoticeIsNotConsent(){
        Store store=new Store();TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);
        assertNull(policy.reserve());assertTrue(policy.initialize(true,"install"));assertNull(policy.reserve());
        assertEquals(1L,store.values.get("epoch"));assertEquals(1L,store.values.get("sequence"));
        assertFalse(policy.noticeShown(false));assertNull(policy.reserve());
        assertTrue(policy.noticeShown(true));assertTrue(policy.reserve().sample);
        assertFalse((Boolean)store.values.get("enabled"));assertFalse(store.values.containsKey("consent"));
    }
    @Test public void legacyAbsenceIsNotFreshOrConsent(){
        Store store=new Store();TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);
        policy.initialize(false,"install");assertEquals("LEGACY_UNDECIDED",store.values.get("origin"));
        assertFalse(policy.enabled());assertTrue(policy.needsNotice());
    }
    @Test public void legacyEnabledMigratesToBasicNoticeWithoutEpochEscape(){
        Store store=new Store();store.values.put("enabled",true);store.values.put("epoch",7L);store.values.put("sequence",12L);
        TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);policy.initialize(false,"install");
        assertEquals(7L,store.values.get("epoch"));assertNull(policy.reserve());
        policy.noticeShown(true);assertEquals(7,policy.reserve().epoch);
    }
    @Test public void oldRefusalsAndPendingRevocationSurviveUpdates(){
        for(boolean pending:new boolean[]{false,true}){
            Store store=new Store();store.values.put("enabled",false);store.values.put("epoch",3L);store.values.put("sequence",7L);store.values.put("revoke_pending",pending);
            TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);policy.initialize(false,"install");
            assertFalse(policy.noticeShown(true));assertFalse(policy.enabled());assertEquals(3L,store.values.get("epoch"));
            assertFalse(new TechnicalMetadataPolicy(store).needsNotice());
            if(pending){assertFalse(policy.resumeBasic(true));assertFalse(policy.reserve().sample);}else assertNull(policy.reserve());
        }
    }
    @Test public void revokeZeroEpochAndRestoredStateNeverEnable(){
        Store store=new Store();store.values.put("revoke_pending",true);
        TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);assertFalse(policy.initialize(false,"install"));assertNull(policy.reserve());
        store=new Store();policy=new TechnicalMetadataPolicy(store);policy.initialize(true,"first");policy.noticeShown(true);
        policy=new TechnicalMetadataPolicy(store);policy.initialize(false,"restored");assertEquals("RESTORED_BLOCKED",policy.mode());
        assertFalse(policy.noticeShown(true));assertNull(policy.reserve());
    }
    @Test public void everyStorageFailureClosesCollectionIncludingCounterReservation(){
        for(int stage=0;stage<4;stage++){
            Store store=new Store();TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);
            if(stage==0)store.fail=true;policy.initialize(true,"install");
            if(stage==1)store.fail=true;policy.noticeShown(true);
            if(stage==2)store.fail=true;policy.reserve();
            if(stage==3){store.fail=true;policy.object();}
            assertTrue(policy.faulted());assertNull(policy.reserve());assertFalse(policy.enabled());
        }
    }
    @Test public void lateResponseDoesNotCancelOfflineRevokeAndLostAckKeepsItPending(){
        Store store=new Store();TechnicalMetadataPolicy policy=new TechnicalMetadataPolicy(store);policy.initialize(true,"install");policy.noticeShown(true);
        TechnicalMetadataPolicy.Ticket old=policy.reserve();policy.object();assertFalse(policy.current(old));
        assertFalse(policy.acknowledge(old));assertTrue(policy.pending());
        TechnicalMetadataPolicy.Ticket revoke=policy.reserve();assertFalse(revoke.sample);assertTrue(policy.pending());
        assertFalse(policy.resumeBasic(true));assertTrue(policy.acknowledge(revoke));assertFalse(policy.pending());
        assertTrue(policy.acknowledge(revoke));assertTrue(policy.resumeBasic(true));assertNull(policy.reserve());
    }
}
