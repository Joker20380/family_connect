package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import org.junit.Test;
import static org.junit.Assert.*;

public class AdmissionDiagnosticsTest {
    private static final String TAG="0123456789abcdef".repeat(4);
    private static final String[] FIELDS={"tcp_admission_waits","tcp_admission_rejected","tcp_admission_timeouts","tcp_admission_cancelled","tcp_admission_waiting","lease_admission_rejected"};
    private DiagnosticRing ring(){return new DiagnosticRing("synthetic","research",84,31);}
    @Test public void admissionCountersSurviveNormalBundleAndReset() throws Exception{
        DiagnosticRing ring=ring();Diagnostics.nativePacket(ring,"{\"limit_denied\":7,\"tcp\":65,\"private_destination\":\"secret\"}");
        JsonObject nativeStats=new JsonObject();nativeStats.addProperty("session_tag",TAG);nativeStats.addProperty("terminal_reason","NONE");
        for(String field:FIELDS)nativeStats.addProperty(field,3);
        nativeStats.addProperty("private_destination","not-exportable");ring.restricted(nativeStats,2,false,100);
        JsonObject bundle=new JsonObject();DiagnosticRing.exportRecord(bundle,"ring",ring.snapshot().toString().getBytes(StandardCharsets.UTF_8),"synthetic");
        JsonObject exported=JsonParser.parseString(new String(DiagnosticRing.exportBytes(bundle),StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("ring");
        assertEquals(7,exported.getAsJsonObject("counters").get("limit_denied").getAsLong());
        for(String field:FIELDS)assertEquals(3,exported.getAsJsonObject("restricted_session").get(field).getAsLong());
        assertFalse(exported.toString().contains("not-exportable"));
        ring.event(new ConnectivityOrchestrator.Event("connect_requested","restricted",null,ConnectivityOrchestrator.State.CONNECTING,0),200);
        assertEquals(0,ring.snapshot().getAsJsonObject("restricted_session").size());
        assertFalse(ring.snapshot().getAsJsonObject("counters").has("limit_denied"));
    }
    @Test public void invalidAndLegacyValuesDoNotBecomeZeros(){
        DiagnosticRing ring=ring();JsonObject input=new JsonObject();input.addProperty("session_tag",TAG);input.addProperty("terminal_reason","NONE");
        ring.restricted(input,2,false,1);
        for(String field:FIELDS)assertFalse(ring.snapshot().getAsJsonObject("restricted_session").has(field));
        input.addProperty(FIELDS[0],-1);input.addProperty(FIELDS[1],0.5);input.addProperty(FIELDS[2],9007199254740992L);input.addProperty(FIELDS[3],"secret");
        ring.restricted(input,2,false,2);Diagnostics.nativePacket(ring,"{\"limit_denied\":-1}");Diagnostics.nativePacket(ring,"{\"limit_denied\":0.5}");
        for(String field:FIELDS)assertFalse(ring.snapshot().getAsJsonObject("restricted_session").has(field));
        assertFalse(ring.snapshot().getAsJsonObject("counters").has("limit_denied"));
    }
    @Test public void lateCleanupDoesNotReplaceFirstSessionCounters(){
        DiagnosticRing ring=ring();JsonObject input=new JsonObject();input.addProperty("session_tag",TAG);input.addProperty("terminal_reason","IO_CLOSED");
        input.addProperty("tcp_admission_rejected",5);ring.restricted(input,3,false,100);
        input.addProperty("tcp_admission_rejected",0);input.addProperty("terminal_reason","CANCELLED");ring.restricted(input,3,false,200);
        JsonObject saved=ring.snapshot().getAsJsonObject("restricted_session");
        assertEquals(5,saved.get("tcp_admission_rejected").getAsLong());assertEquals("IO_CLOSED",saved.get("terminal_reason").getAsString());
    }
}
