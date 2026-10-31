package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class StartupFidelityTest {
    private JsonObject nativeRecord(int attempt,long started,String cause){
        return JsonParser.parseString("{\"schema\":1,\"attempt\":"+attempt+",\"started_unix_ms\":"+started+",\"observed_ms\":10,\"completed_ms\":12,\"complete\":true,\"status\":\"FAILED\",\"stage\":\"HELLO_RECEIVE\",\"cause\":\""+cause+"\",\"observation\":{\"point\":\"FAMILY_RECEIVE\",\"error_category\":\""+cause+"\",\"context_state\":\"LIVE\",\"stop_at_observation\":\"NONE\",\"elapsed_ms\":9,\"raw_error\":\"secret\"},\"local_stop\":{\"source\":\"CLEANUP\",\"elapsed_ms\":11},\"private\":\"secret\"}").getAsJsonObject();
    }
    private DiagnosticRing ring(){
        DiagnosticRing ring=new DiagnosticRing("synthetic","research",84,31);
        ring.event(new ConnectivityOrchestrator.Event("connect_requested","restricted",null,ConnectivityOrchestrator.State.CONNECTING,0),100);
        return ring;
    }
    private void stats(DiagnosticRing ring,JsonObject record){JsonObject input=new JsonObject();input.add("owner_startup",record);ring.startupStats(input);}
    @Test public void normalPersistedExportKeepsFactsAndSeparatesIncident()throws Exception{
        DiagnosticRing ring=ring();stats(ring,nativeRecord(1,101,"IO_DEADLINE"));
        Path incident=Files.createTempFile("synthetic-incident-",".json"),current=Files.createTempFile("synthetic-ring-",".json");
        try{
            Files.write(incident,ring.snapshot().toString().getBytes(StandardCharsets.UTF_8));
            stats(ring,nativeRecord(1,101,"CANCELLED"));ring.cleanup(true,120);
            assertEquals("IO_DEADLINE",ring.snapshot().getAsJsonObject("restricted_startup").get("cause").getAsString());
            ring.event(new ConnectivityOrchestrator.Event("connect_requested","restricted",null,ConnectivityOrchestrator.State.CONNECTING,0),200);
            stats(ring,nativeRecord(1,101,"UNKNOWN"));
            assertEquals(0,ring.snapshot().getAsJsonObject("restricted_startup").size());
            JsonObject drain=nativeRecord(2,201,"CANCELLED");drain.addProperty("stage","OWNERSHIP_DRAIN");
            drain.getAsJsonObject("observation").addProperty("stop_at_observation","STARTUP_BUDGET");
            drain.getAsJsonObject("local_stop").addProperty("source","STARTUP_BUDGET");stats(ring,drain);
            Files.write(current,ring.snapshot().toString().getBytes(StandardCharsets.UTF_8));
            JsonObject bundle=new JsonObject();
            DiagnosticRing.exportRecord(bundle,"ring",Files.readAllBytes(current),"synthetic");
            DiagnosticRing.exportRecord(bundle,"incident",Files.readAllBytes(incident),"synthetic");
            byte[] encoded=DiagnosticRing.exportBytes(bundle);
            JsonObject exported=JsonParser.parseString(new String(encoded,StandardCharsets.UTF_8)).getAsJsonObject();
            JsonObject first=exported.getAsJsonObject("incident").getAsJsonObject("restricted_startup");
            assertEquals("IO_DEADLINE",first.get("cause").getAsString());
            assertEquals("LIVE",first.getAsJsonObject("observation").get("context_state").getAsString());
            assertEquals("NONE",first.getAsJsonObject("observation").get("stop_at_observation").getAsString());
            assertEquals("CLEANUP",first.getAsJsonObject("local_stop").get("source").getAsString());
            assertEquals("OWNERSHIP_DRAIN",exported.getAsJsonObject("ring").getAsJsonObject("restricted_startup").get("stage").getAsString());
            assertNotEquals(exported.getAsJsonObject("ring").get("connection_id"),exported.getAsJsonObject("incident").get("connection_id"));
            assertFalse(new String(encoded,StandardCharsets.UTF_8).contains("secret"));
        }finally{Files.deleteIfExists(current);Files.deleteIfExists(incident);}
    }
    @Test public void oldSchemaMissingAndUnknownFieldsRemainCompatible()throws Exception{
        JsonObject legacy=nativeRecord(1,101,"UNKNOWN");legacy.remove("observation");legacy.remove("local_stop");
        DiagnosticRing ring=ring();stats(ring,legacy);
        JsonObject projected=ring.snapshot().getAsJsonObject("restricted_startup");
        assertFalse(projected.has("observation"));assertFalse(projected.has("local_stop"));
        assertEquals("UNKNOWN",projected.get("cause").getAsString());
        for(String cause:new String[]{"CLOSED_PIPE","DEADLINE","TIMEOUT_UNQUALIFIED","PROTOCOL_REJECTED","CERTIFICATE_AUTHORITY"})
            assertEquals(cause,RestrictedStartup.project(nativeRecord(2,201,cause)).get("cause").getAsString());
        JsonObject unsafe=nativeRecord(3,301,"UNKNOWN");unsafe.getAsJsonObject("observation").addProperty("context_state","secret");
        assertEquals("UNKNOWN",RestrictedStartup.project(unsafe).getAsJsonObject("observation").get("context_state").getAsString());
        assertThrows(IOException.class,()->DiagnosticRing.exportRecord(new JsonObject(),"ring",new byte[DiagnosticRing.RECORD_LIMIT+1],"synthetic"));
        JsonObject huge=new JsonObject();huge.addProperty("data","x".repeat(DiagnosticRing.EXPORT_LIMIT));
        assertThrows(IOException.class,()->DiagnosticRing.exportBytes(huge));
    }
}
