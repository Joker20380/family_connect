package com.familyconnect.app;

import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class BootstrapCorrelationTest {
    private JsonObject receipt()throws Exception{
        try(InputStream input=getClass().getResourceAsStream("/bootstrap-deadline-native.json")){
            assertNotNull("real lease fixture receipt required",input);
            return JsonParser.parseString(new String(input.readAllBytes(),StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }
    private String tag(JsonObject startup){return startup.getAsJsonArray("bootstrap_exchanges").get(0).getAsJsonObject().get("bootstrap_exchange_tag").getAsString();}
    @Test public void realPreHelloReceiptSurvivesNormalBundle()throws Exception{
        JsonObject receipt=receipt(),startup=receipt.getAsJsonObject("owner_startup");
        long started=startup.get("started_unix_ms").getAsLong();
        DiagnosticRing ring=new DiagnosticRing("synthetic","research",84,31);
        ring.event(new ConnectivityOrchestrator.Event("connect_requested","restricted",null,ConnectivityOrchestrator.State.CONNECTING,0),started-1);
        Diagnostics.nativeStartup(ring,startup.toString());
        String expected=tag(startup);
        Path incident=Files.createTempFile("correlation-incident-",".json");
        try{
            Files.write(incident,ring.snapshot().toString().getBytes(StandardCharsets.UTF_8));
            JsonObject late=startup.deepCopy();late.addProperty("cause","CANCELLED");late.getAsJsonArray("bootstrap_exchanges").get(0).getAsJsonObject().addProperty("bootstrap_exchange_tag","f".repeat(64));
            Diagnostics.nativeStartup(ring,late.toString());ring.cleanup(true,started+3000);
            assertEquals(expected,tag(ring.snapshot().getAsJsonObject("restricted_startup")));
            ring.event(new ConnectivityOrchestrator.Event("connect_requested","restricted",null,ConnectivityOrchestrator.State.CONNECTING,0),started+4000);
            Diagnostics.nativeStartup(ring,late.toString());
            assertEquals(0,ring.snapshot().getAsJsonObject("restricted_startup").size());
            JsonObject bundle=new JsonObject();
            DiagnosticRing.exportRecord(bundle,"incident",Files.readAllBytes(incident),"synthetic");
            DiagnosticRing.exportRecord(bundle,"ring",ring.snapshot().toString().getBytes(StandardCharsets.UTF_8),"synthetic");
            JsonObject exported=JsonParser.parseString(new String(DiagnosticRing.exportBytes(bundle),StandardCharsets.UTF_8)).getAsJsonObject();
            JsonObject actual=exported.getAsJsonObject("incident").getAsJsonObject("restricted_startup");
            assertEquals(expected,tag(actual));
            assertEquals(startup.get("cause"),actual.get("cause"));
            assertEquals("HELLO_RECEIVE",actual.get("stage").getAsString());
            assertEquals(startup.get("observation"),actual.get("observation"));
            assertEquals("CLEANUP",actual.getAsJsonObject("local_stop").get("source").getAsString());
            boolean matched=false;
            for(JsonElement element:receipt.getAsJsonObject("ownership").getAsJsonArray("events")){
                JsonObject event=element.getAsJsonObject();
                if(event.has("exchange")&&expected.equals(event.get("exchange").getAsString())&&"wait".equals(event.get("action").getAsString())){
                    assertEquals(receipt.get("holder_dedicated_tag"),event.get("generation"));
                    assertEquals("true",event.get("same_identity").getAsString());matched=true;
                }
            }
            assertTrue("export must match real server wait",matched);
            assertFalse(actual.has("session_tag"));
        }finally{Files.deleteIfExists(incident);}
    }
    @Test public void optionalLegacyPrivacyAndBound()throws Exception{
        JsonObject startup=receipt().getAsJsonObject("owner_startup");
        JsonObject legacy=startup.deepCopy();legacy.remove("bootstrap_exchanges");legacy.getAsJsonObject("observation").remove("bootstrap_exchange_tag");legacy.addProperty("cause","UNKNOWN");
        assertFalse(RestrictedStartup.project(legacy).has("bootstrap_exchanges"));
        assertEquals("UNKNOWN",RestrictedStartup.project(legacy).get("cause").getAsString());
        JsonArray entries=startup.getAsJsonArray("bootstrap_exchanges");
        JsonObject first=entries.get(0).getAsJsonObject();first.addProperty("nonce","secret");first.addProperty("room_url","secret");
        first.addProperty("family_authenticated",false);
        for(int index=0;index<7;index++)entries.add(first.deepCopy());
        startup.addProperty("bootstrap_exchanges_dropped",2);
        JsonObject safe=RestrictedStartup.project(startup);
        assertEquals(4,safe.getAsJsonArray("bootstrap_exchanges").size());
        assertEquals(6,safe.get("bootstrap_exchanges_dropped").getAsLong());
        assertFalse(safe.getAsJsonArray("bootstrap_exchanges").get(0).getAsJsonObject().get("family_authenticated").getAsBoolean());
        assertFalse(safe.toString().contains("secret"));
        first.addProperty("bootstrap_exchange_tag","https://private.invalid");
        assertFalse(RestrictedStartup.project(startup).toString().contains("private.invalid"));
    }
}
