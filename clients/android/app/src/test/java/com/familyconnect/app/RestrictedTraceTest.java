package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedTraceTest {
    @Test public void reliableCauseAndProgressAreSafeAndPreserved(){
        for(String reason:new String[]{"RELIABLE_HANDSHAKE_TIMEOUT","RELIABLE_FRAME_TIMEOUT","RELIABLE_RETRY_EXHAUSTED"}){
            JsonObject source=snapshot(1),first=event(1,reason);
            first.addProperty("stage","CARRIER");first.addProperty("state","FAILED");
            first.addProperty("reliable_pending",8);first.addProperty("reliable_retries",8);
            first.addProperty("reliable_age_ms",9000);first.addProperty("reliable_ack_received",17);
            first.addProperty("reliable_ack_age_ms",1000);first.addProperty("reliable_progress_age_ms",9000);
            first.addProperty("reliable_sacked",0);first.addProperty("reliable_payload","secret-payload");
            source.add("first_failure",first);
            JsonObject safe=RestrictedTrace.project(source,TAG);
            JsonObject cause=safe.getAsJsonObject("first_failure");
            assertEquals(reason,cause.get("reason").getAsString());
            assertEquals(17,cause.get("reliable_ack_received").getAsInt());
            assertEquals(0,cause.get("reliable_sacked").getAsInt());
            assertFalse(safe.toString().contains("secret"));
            JsonObject nativeValue=new JsonObject();nativeValue.addProperty("session_tag",TAG);nativeValue.add("lifecycle",source);
            DiagnosticRing ring=new DiagnosticRing("FC-YHQB-9VJN","diagnostic",61,30);
            ring.restricted(nativeValue,3,false,100);
            assertEquals(reason,RestrictedTrace.firstReason(ring.snapshot().getAsJsonObject("restricted_session")));
            assertEquals(reason,DiagnosticRing.Code.valueOf(reason).name());
            first.addProperty("reliable_age_ms",-1);first.addProperty("reliable_retries",1.5);
            cause=RestrictedTrace.project(source,TAG).getAsJsonObject("first_failure");
            assertFalse(cause.has("reliable_age_ms"));assertFalse(cause.has("reliable_retries"));
        }
    }
    static final String TAG="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
    private static JsonObject event(long sequence,String reason){
        JsonObject event=new JsonObject();event.addProperty("session_tag",TAG);event.addProperty("sequence",sequence);
        event.addProperty("timestamp_ms",100+sequence);event.addProperty("stage","WEBSOCKET");event.addProperty("state","CLOSED");
        event.addProperty("reason",reason);event.addProperty("close_code",1006);event.addProperty("raw_reason","secret-room-token");return event;
    }
    static JsonObject snapshot(int size){
        JsonObject source=new JsonObject();source.addProperty("session_tag",TAG);source.addProperty("correlation_status","VALID");
        JsonArray trace=new JsonArray();for(int index=1;index<=size;index++)trace.add(event(index,"NONE"));
        source.add("trace",trace);source.add("first_failure",event(1,"SIGNAL_WS_CLOSE"));return source;
    }
    @Test public void projectionBoundPrivacyAndMalformed(){
        JsonObject safe=RestrictedTrace.project(snapshot(200),TAG);
        assertEquals(192,safe.getAsJsonArray("trace").size());assertEquals(8,safe.get("projection_dropped").getAsInt());
        assertEquals("SIGNAL_WS_CLOSE",safe.getAsJsonObject("first_failure").get("reason").getAsString());
        assertFalse(safe.toString().contains("secret"));assertNull(RestrictedTrace.project(snapshot(1),TAG.substring(0,32)));
        assertNull(RestrictedTrace.project(snapshot(1),""));assertNull(RestrictedTrace.project(new JsonPrimitive("secret"),TAG));
        JsonObject bad=event(1,"secret");assertNull(RestrictedTrace.event(bad,TAG));
        bad=event(1,"NONE");bad.addProperty("sequence",1.5);assertNull(RestrictedTrace.event(bad,TAG));
        bad=event(1,"NONE");bad.addProperty("session_tag",TAG.replace('a','b'));assertNull(RestrictedTrace.event(bad,TAG));
    }
    @Test public void terminalUpdatesKeepFirstAndBindHistory(){
        DiagnosticRing ring=new DiagnosticRing("FC-YHQB-9VJN","0.1.18-beta61",61,30);
        JsonObject source=new JsonObject();source.addProperty("session_tag",TAG);source.addProperty("terminal_reason","IO_CLOSED");
        source.add("lifecycle",snapshot(1));ring.restricted(source,3,false,100);
        String connection=ring.snapshot().get("connection_id").getAsString();
        JsonObject next=snapshot(3);next.add("first_failure",event(2,"FAMILY_TLS_EOF"));source.add("lifecycle",next);
        ring.restricted(source,3,false,200);
        JsonObject session=ring.snapshot().getAsJsonObject("restricted_session");
        assertEquals(connection,session.get("connection_id").getAsString());
        assertEquals("SIGNAL_WS_CLOSE",RestrictedTrace.firstReason(session));
        assertEquals(3,session.getAsJsonObject("lifecycle").getAsJsonArray("trace").size());
        source.addProperty("session_tag",TAG.replace('a','b'));source.remove("lifecycle");ring.restricted(source,2,false,300);
        assertEquals(TAG,ring.snapshot().getAsJsonArray("restricted_history").get(0).getAsJsonObject().get("session_tag").getAsString());
        assertEquals(1,ring.snapshot().getAsJsonArray("restricted_history").size());
        ring.cleanup(false,400);assertEquals("RECOVERY_CLEANUP_FAILED",ring.snapshot().getAsJsonArray("events").get(0).getAsJsonObject().get("reason_code").getAsString());
    }
    @Test public void fullHistoryAndTwoSnapshotsFitExportBudget(){
        DiagnosticRing ring=new DiagnosticRing("FC-YHQB-9VJN","0.1.18-beta61",61,30);
        for(int index=0;index<128;index++)ring.nativeEvent("bootstrap_family_auth",Long.MAX_VALUE);
        for(int index=1;index<=6;index++){
            String tag=String.format(java.util.Locale.ROOT,"%064x",index);
            JsonObject lifecycle=snapshot(192);lifecycle.addProperty("session_tag",tag);
            lifecycle.getAsJsonObject("first_failure").addProperty("session_tag",tag);
            lifecycle.getAsJsonObject("first_failure").add("delivery",RestrictedDeliveryTest.largestFixture());
            for(JsonElement element:lifecycle.getAsJsonArray("trace")){
                JsonObject entry=element.getAsJsonObject();entry.addProperty("session_tag",tag);
                entry.addProperty("tx",9007199254740991L);entry.addProperty("rx",9007199254740991L);
                entry.add("delivery",RestrictedDeliveryTest.largestFixture());
                entry.addProperty("heartbeat_kind","APPLICATION");entry.addProperty("close_reason","READ_TIMEOUT");entry.addProperty("target","SUBSCRIBER");
            }
            JsonObject source=new JsonObject();source.addProperty("session_tag",tag);source.addProperty("terminal_reason","NONE");source.add("lifecycle",lifecycle);
            ring.restricted(source,2,false,index);
        }
        JsonObject snapshot=ring.snapshot();assertEquals(4,snapshot.getAsJsonArray("restricted_history").size());
        assertTrue(snapshot.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<DiagnosticRing.RECORD_LIMIT);
        JsonObject bundle=new JsonObject();bundle.add("ring",snapshot);bundle.add("incident",snapshot.deepCopy());
        assertTrue(bundle.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<DiagnosticRing.EXPORT_LIMIT);
    }
}
