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
    @Test public void projectsNativeTerminalAndPreservesFirstFailure(){
        DiagnosticRing ring=ring();JsonObject input=new JsonObject();
        input.addProperty("session_tag","0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef");
        input.addProperty("terminal_reason","IO_CLOSED");input.addProperty("reliable_terminal","recovery_exhausted");
        input.addProperty("signaling_failure","close_code_1006");input.addProperty("ice_failure","SUBSCRIBER_disconnected");
        input.addProperty("retransmissions",8);input.addProperty("terminal_at_ms",123);
        input.addProperty("room_url","https://private/?token=secret");
        input.addProperty("publisher_state","private-peer");input.addProperty("received_bytes",-1);
        input.addProperty("sent_bytes",1.5);input.addProperty("sent_frames",9007199254740992L);
        ring.restricted(input,3,false,130);
        JsonObject captured=ring.snapshot().getAsJsonObject("restricted_session");
        assertEquals("IO_CLOSED",captured.get("terminal_reason").getAsString());
        assertEquals("recovery_exhausted",captured.get("reliable_terminal").getAsString());
        assertEquals(130,captured.get("terminal_observed_at_ms").getAsLong());
        assertEquals("UNKNOWN",captured.get("publisher_state").getAsString());
        assertFalse(captured.has("room_url"));assertFalse(captured.has("received_bytes"));
        assertFalse(captured.has("sent_bytes"));assertFalse(captured.has("sent_frames"));
        assertFalse(captured.toString().contains("private"));
        input.addProperty("terminal_reason","CANCELLED");ring.restricted(input,3,true,140);
        assertEquals(captured,ring.snapshot().getAsJsonObject("restricted_session"));
        captured.addProperty("terminal_reason","tampered");
        assertEquals("IO_CLOSED",ring.snapshot().getAsJsonObject("restricted_session").get("terminal_reason").getAsString());
        ring.event(event("connect_requested",ConnectivityOrchestrator.State.CONNECTING,null),150);
        assertEquals(0,ring.snapshot().getAsJsonObject("restricted_session").size());
    }
    @Test public void recordsDeniedWithoutInventingNetworkCause(){
        DiagnosticRing ring=ring();JsonObject input=new JsonObject();
        input.addProperty("terminal_reason","NONE");input.addProperty("session_tag","private tag");
        input.addProperty("signaling_failure","private server error");
        ring.restricted(input,2,false,1);
        assertFalse(ring.snapshot().getAsJsonObject("restricted_session").has("terminal_observed_at_ms"));
        ring.restricted(input,2,true,2);
        JsonObject captured=ring.snapshot().getAsJsonObject("restricted_session");
        assertEquals("NONE",captured.get("terminal_reason").getAsString());
        assertTrue(captured.get("authorization_denied").getAsBoolean());
        assertEquals(2,captured.get("terminal_observed_at_ms").getAsLong());
        assertFalse(captured.toString().contains("private"));
    }
}
