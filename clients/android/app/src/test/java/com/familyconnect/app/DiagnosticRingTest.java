package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class DiagnosticRingTest {
    private DiagnosticRing ring(){return new DiagnosticRing("random-support-id","0.1.18-beta59",59,31);}
    private ConnectivityOrchestrator.Event event(String name,ConnectivityOrchestrator.State state,ConnectivityOrchestrator.Failure failure){return new ConnectivityOrchestrator.Event(name,"tcp",failure,state,123);}
    @Test public void capturesBothFailureTransitionsAndCorrelates(){
        DiagnosticRing ring=ring();ring.event(event("connect_requested",ConnectivityOrchestrator.State.CONNECTING,null),1);
        String connection=ring.snapshot().get("connection_id").getAsString();
        ring.vpn(true,2);ring.readiness(true,2);
        assertTrue(ring.event(event("connect_failed",ConnectivityOrchestrator.State.FAILED,ConnectivityOrchestrator.Failure.NETWORK),3));
        assertEquals(connection,ring.snapshot().get("connection_id").getAsString());assertTrue(ring.snapshot().get("vpn_capture_open").getAsBoolean());
        assertFalse(ring.event(event("connect_failed",ConnectivityOrchestrator.State.FAILED,ConnectivityOrchestrator.Failure.NETWORK),4));
        ring.event(event("candidate_succeeded",ConnectivityOrchestrator.State.CONNECTED,null),5);
        ring.event(event("restoration_attempted",ConnectivityOrchestrator.State.RESTORING,ConnectivityOrchestrator.Failure.NETWORK),6);
        assertTrue(ring.event(event("restoration_failed",ConnectivityOrchestrator.State.FAILED,ConnectivityOrchestrator.Failure.NETWORK),7));
    }
    @Test public void boundsAndProjectsUntrustedNativeFields(){
        DiagnosticRing ring=ring();for(int index=0;index<1000;index++)ring.nativeEvent("bootstrap_family_auth",index);
        ring.nativeEvent("https://room.example/?token=private",1001);ring.counter("private_key",7);ring.counter("dns",44);ring.counter("tcp",-1);ring.network("private-SSID");
        JsonObject value=ring.snapshot();assertEquals(128,value.getAsJsonArray("events").size());
        assertEquals(44,value.getAsJsonObject("counters").get("dns").getAsLong());
        assertEquals("UNKNOWN",value.get("network_class").getAsString());assertFalse(value.toString().contains("private"));
        value.getAsJsonArray("events").remove(0);assertEquals(128,ring.snapshot().getAsJsonArray("events").size());
    }
    @Test public void preservesTypedReadinessAndNewConnectionIds(){
        DiagnosticRing ring=ring();ring.readinessResult(ReadinessImportResult.Code.EXPIRED_ON_IMPORT,1);
        assertEquals("EXPIRED_ON_IMPORT",ring.snapshot().get("restricted_readiness").getAsString());
        String old=ring.snapshot().get("connection_id").getAsString();ring.event(event("connect_requested",ConnectivityOrchestrator.State.CONNECTING,null),2);
        assertNotEquals(old,ring.snapshot().get("connection_id").getAsString());
    }
}
