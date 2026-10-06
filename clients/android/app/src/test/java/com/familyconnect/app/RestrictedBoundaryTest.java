package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedBoundaryTest {
    static JsonObject point(int index){
        JsonObject point=new JsonObject();
        point.addProperty("index",index);point.addProperty("at_ms",1);
        point.addProperty("stage","rtp_written");point.addProperty("result","ok");point.addProperty("direction","tx");
        point.addProperty("data_known",true);point.addProperty("data_sequence",48);
        point.addProperty("attempt_known",true);point.addProperty("attempt",1);
        point.addProperty("message_known",true);point.addProperty("message",9);
        point.addProperty("payload","PRIVATE KEY token https://secret");return point;
    }
    @Test public void boundedAndNoFreeText(){
        JsonObject source=new JsonObject();source.addProperty("dropped",10);JsonArray events=new JsonArray();
        for(int index=1;index<=100;index++)events.add(point(index));source.add("events",events);
        JsonObject safe=RestrictedDelivery.boundaries(source);
        assertEquals(64,safe.getAsJsonArray("events").size());assertEquals(36,safe.get("projection_dropped").getAsInt());
        assertFalse(safe.toString().contains("secret"));assertFalse(safe.toString().contains("payload"));
        assertEquals(1,safe.getAsJsonArray("events").get(0).getAsJsonObject().get("attempt").getAsInt());
    }
    @Test public void unknownDoesNotBecomeAttemptZero(){
        JsonObject source=new JsonObject();source.addProperty("dropped",0);JsonArray events=new JsonArray();
        JsonObject point=point(1);point.remove("attempt");point.remove("attempt_known");events.add(point);source.add("events",events);
        JsonObject safe=RestrictedDelivery.boundaries(source).getAsJsonArray("events").get(0).getAsJsonObject();
        assertFalse(safe.has("attempt_known"));assertFalse(safe.has("attempt"));
        point.addProperty("stage","https://secret");assertEquals(0,RestrictedDelivery.boundaries(source).getAsJsonArray("events").size());
    }
    @Test public void invalidRangesRejected(){
        for(String field:new String[]{"attempt","first_rtp","timestamp","data_sequence"}){
            JsonObject source=new JsonObject();source.addProperty("dropped",0);JsonArray events=new JsonArray();
            JsonObject point=point(1);point.addProperty(field,9007199254740992L);events.add(point);source.add("events",events);
            assertEquals(0,RestrictedDelivery.boundaries(source).getAsJsonArray("events").size());
        }
    }
    @Test public void survivesNativeProjectionWithinExportBudget(){
        DiagnosticRing ring=new DiagnosticRing("FC-YHQB-9VJN","diagnostic",65,30);
        for(int session=0;session<8;session++){
            String tag=String.format("%064x",session+1);
            JsonObject lifecycle=RestrictedTraceTest.snapshot(192);
            lifecycle.addProperty("session_tag",tag);
            lifecycle.getAsJsonObject("first_failure").addProperty("session_tag",tag);
            for(JsonElement entry:lifecycle.getAsJsonArray("trace")){
                entry.getAsJsonObject().addProperty("session_tag",tag);
                entry.getAsJsonObject().add("delivery",RestrictedDeliveryTest.largestFixture());
            }
            JsonObject boundaries=new JsonObject();boundaries.addProperty("dropped",1000);JsonArray entries=new JsonArray();
            for(int index=1;index<=64;index++){
                JsonObject point=point(index);
                for(String field:"sender message timestamp media_track packets ack_mask".split(" "))point.addProperty(field,4294967295L);
                for(String field:"at_ms data_sequence ack_base".split(" "))point.addProperty(field,9007199254740991L);
                entries.add(point);
            }
            boundaries.add("events",entries);lifecycle.add("boundaries",boundaries);
            JsonObject source=new JsonObject();source.addProperty("session_tag",tag);source.add("lifecycle",lifecycle);
            ring.restricted(source,2,false,session);
        }
        JsonObject snapshot=ring.snapshot();
        assertEquals(64,snapshot.getAsJsonObject("restricted_session").getAsJsonObject("lifecycle").getAsJsonObject("boundaries").getAsJsonArray("events").size());
        assertTrue(snapshot.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<DiagnosticRing.RECORD_LIMIT);
        assertFalse(snapshot.toString().contains("PRIVATE KEY"));
    }
}
