package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedTraceTest {
    private static final String TAG="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
    private JsonObject event(long sequence,String reason){
        JsonObject event=new JsonObject();event.addProperty("session_tag",TAG);event.addProperty("sequence",sequence);
        event.addProperty("timestamp_ms",100+sequence);event.addProperty("stage","WEBSOCKET");event.addProperty("state","CLOSED");
        event.addProperty("reason",reason);event.addProperty("close_code",1006);event.addProperty("raw_reason","secret-room-token");return event;
    }
    private JsonObject snapshot(int size){
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
}
