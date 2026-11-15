package com.familyconnect.app;

import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class TechnicalMetadataTest {
    @Test public void consentEpochAndSequenceDetermineUniqueIdentity(){
        JsonObject first=TechnicalMetadataSnapshot.report(1,2,true,new JsonObject());
        assertEquals("00000000000000010000000000000002",first.get("report_id").getAsString());
        assertNotEquals(first.get("report_id"),TechnicalMetadataSnapshot.report(2,2,true,new JsonObject()).get("report_id"));
    }
    @Test public void revokeContainsNoOldObservations(){
        JsonObject prior=new JsonObject();prior.addProperty("model","private test value");
        JsonObject revoked=TechnicalMetadataSnapshot.report(2,3,false,prior);
        assertEquals("revoke",revoked.get("operation").getAsString());
        assertEquals(0,revoked.getAsJsonObject("observations").size());
        assertFalse(revoked.toString().contains("private"));
    }
    @Test public void onlyEstablishedSessionHasActiveTransport(){
        for(String state:new String[]{"CONNECTING","DISCONNECTED","FAILED","STOPPING","RESTORING"}){
            JsonObject session=TechnicalMetadataSnapshot.session("auto","TCP","awg","ru",state);
            assertEquals("AUTO",session.get("preference").getAsString());
            assertEquals("TCP",session.get("attempt").getAsString());
            assertEquals("NONE",session.get("transport").getAsString());
            assertEquals("UNKNOWN",session.get("gateway").getAsString());
        }
    }
    @Test public void autoShowsActualNotPreferredTransport(){
        JsonObject session=TechnicalMetadataSnapshot.session("auto","NONE","restricted","nl-amsterdam-2","CONNECTED");
        assertEquals("MESH",session.get("transport").getAsString());
        assertEquals("nl-amsterdam-2",session.get("gateway").getAsString());
        assertEquals("AUTO",session.get("preference").getAsString());
    }
    @Test public void valuesAreBoundedNotRawLogs(){
        assertEquals("abcdef",TechnicalMetadataSnapshot.text("abc\ndef\u0000",6));
        assertNull(TechnicalMetadataSnapshot.text("  ",20));
        assertEquals("UNKNOWN",TechnicalMetadataSnapshot.gateway("not-a-registry-node"));
    }
    @Test public void canonicalGatewayIsNotLostAtSessionSerialization(){
        for(String raw:new String[]{"ru","gateway-ru","nl","nl-amsterdam-1","nl-amsterdam-2"}){
            String canonical=TechnicalMetadataSnapshot.gateway(raw);
            assertEquals(canonical,TechnicalMetadataSnapshot.session("auto","NONE","awg",canonical,"CONNECTED").get("gateway").getAsString());
        }
        assertEquals("gateway-ru",TechnicalMetadataSnapshot.gateway("ru"));
    }
    @Test public void onlyOneUploadAndCompletionBasedMinimumInterval(){
        TechnicalMetadataSchedule schedule=new TechnicalMetadataSchedule();
        assertTrue(schedule.begin(0,false));assertFalse(schedule.begin(100000,false));
        schedule.finish(10000,true);assertEquals(60000,schedule.delay(10000,false));
        assertFalse(schedule.begin(69999,false));assertTrue(schedule.begin(70000,false));
    }
    @Test public void revokeBypassesSampleCooldownButCannotRunAlongsideOldRequest(){
        TechnicalMetadataSchedule schedule=new TechnicalMetadataSchedule();assertTrue(schedule.begin(0,false));
        schedule.revoke();assertFalse(schedule.begin(1,true));schedule.finish(1000,false);
        schedule.revoke();assertTrue(schedule.begin(1001,true));
    }
    @Test public void failureBackoffIsBoundedAndCannotBeResetByNetworkNoise(){
        TechnicalMetadataSchedule schedule=new TechnicalMetadataSchedule();long now=0;
        for(int count=0;count<12;count++){
            assertTrue(schedule.begin(now,false));schedule.finish(now,false);
            long delay=schedule.delay(now,false);assertTrue(delay>=60000&&delay<=1800000);
            assertFalse(schedule.begin(now+delay-1,false));now+=delay;
        }
    }
    @Test public void terminalTimestampOnlyCollectedWithSeparateConsent(){
        ConnectionTerminal terminal=new ConnectionTerminal();
        terminal.end(terminal.begin(ConnectionTerminal.Stage.AWG),ConnectionTerminal.Stage.FAILED,false);
        assertEquals(0,terminal.snapshot().failureAt);
        terminal.observeTechnical(true);
        terminal.end(terminal.begin(ConnectionTerminal.Stage.TCP),ConnectionTerminal.Stage.AUTH,false);
        assertTrue(terminal.snapshot().failureAt>0);assertEquals(ConnectionTerminal.Stage.AUTH,terminal.snapshot().failureStage);
        terminal.begin(ConnectionTerminal.Stage.AWG);assertTrue(terminal.snapshot().failureAt>0);
        terminal.observeTechnical(false);assertEquals(0,terminal.snapshot().failureAt);assertNull(terminal.snapshot().failureStage);
    }
}
