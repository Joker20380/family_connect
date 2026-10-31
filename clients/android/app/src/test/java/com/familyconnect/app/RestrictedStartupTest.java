package com.familyconnect.app;

import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedStartupTest {
    private JsonObject result(long attempt,long started,boolean complete){
        JsonObject value=new JsonObject();value.addProperty("schema",1);value.addProperty("attempt",attempt);
        value.addProperty("started_unix_ms",started);value.addProperty("status",complete?"FAILED":"RUNNING");
        value.addProperty("stage","SEED_ADMISSION");value.addProperty("cause",complete?"DEADLINE":"NONE");
        value.addProperty("complete",complete);value.addProperty("directory_fingerprint",RestrictedTraceTest.TAG);
        value.addProperty("raw_error","private-room-url");return value;
    }
    @Test public void publicResultKeepsSafeSeedCauseAndRejectsMalformed(){
        JsonObject safe=RestrictedStartup.project(result(4,100,true));
        assertEquals("SEED_ADMISSION",safe.get("stage").getAsString());
        assertEquals("DEADLINE",safe.get("cause").getAsString());
        assertEquals(RestrictedTraceTest.TAG,safe.get("directory_fingerprint").getAsString());
        assertFalse(safe.toString().contains("private"));
        JsonObject invalid=result(4,100,true);invalid.addProperty("cause","private-exception");
        assertEquals("UNKNOWN",RestrictedStartup.project(invalid).get("cause").getAsString());
        invalid.addProperty("complete","true");assertNull(RestrictedStartup.project(invalid));
    }
    @Test public void ringRejectsOldProcessAttemptAndCleanupOverwrite(){
        DiagnosticRing ring=new DiagnosticRing("support","research",80,31);
        ring.event(new ConnectivityOrchestrator.Event("connect_requested","restricted",null,ConnectivityOrchestrator.State.CONNECTING,0),100);
        ring.startup(result(99,90,true));assertEquals(0,ring.snapshot().getAsJsonObject("restricted_startup").size());
        ring.startup(result(4,101,true));ring.startup(result(4,101,false));ring.startup(result(3,101,false));
        JsonObject saved=ring.snapshot().getAsJsonObject("restricted_startup");
        assertEquals(4,saved.get("attempt").getAsInt());assertTrue(saved.get("complete").getAsBoolean());
        ring.startup(result(5,110,false));assertEquals(5,ring.snapshot().getAsJsonObject("restricted_startup").get("attempt").getAsInt());
    }
    @Test public void firstCloseSurvivesAndroidProjection(){
        JsonObject source=RestrictedTraceTest.snapshot(200);
        JsonObject first=source.getAsJsonObject("first_failure").deepCopy();
        first.addProperty("close_source","SIGNAL_READ");first.addProperty("lease_deadline_ms",1791650000000L);
        source.add("first_close",first);
        JsonObject safe=RestrictedTrace.project(source,RestrictedTraceTest.TAG).getAsJsonObject("first_close");
        assertEquals("SIGNAL_READ",safe.get("close_source").getAsString());
        assertEquals(1791650000000L,safe.get("lease_deadline_ms").getAsLong());assertFalse(safe.toString().contains("secret"));
    }
}
