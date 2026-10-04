package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedDeliveryTest {
    static JsonObject fixture(){
        JsonObject delivery=new JsonObject(),flow=new JsonObject(),assembly=new JsonObject(),point=new JsonObject();
        for(String key:"send_base send_next receive_next receive_mask ack_base ack_mask pending buffered head_retries".split(" "))flow.addProperty(key,0);
        flow.addProperty("send_next",8);flow.addProperty("pending",8);flow.addProperty("ack_mask",254);
        flow.addProperty("ack_seen",true);flow.addProperty("head_sacked",false);
        for(String key:"fragments completed expired malformed duplicate conflict capacity crc_failed recent pending rtp rtp_gaps vp8_frames".split(" "))assembly.addProperty(key,0);
        assembly.addProperty("pending",1);
        point.addProperty("sender",1);point.addProperty("message",42);point.addProperty("total",3);point.addProperty("mask",6);
        point.addProperty("data_known",false);point.addProperty("data_sequence",0);
        delivery.add("flow",flow);delivery.add("assembly",assembly);
        for(String key:new String[]{"pending","queued","written","received"})delivery.add(key,point.deepCopy());
        return delivery;
    }
    static JsonObject largestFixture(){
        JsonObject value=fixture(),flow=value.getAsJsonObject("flow");
        for(String field:new String[]{"send_base","send_next","receive_next","ack_base"})flow.addProperty(field,9007199254740991L);
        for(String field:new String[]{"receive_mask","ack_mask"})flow.addProperty(field,4294967295L);
        for(String field:new String[]{"pending","buffered","head_retries"})flow.addProperty(field,32);
        JsonObject assembly=value.getAsJsonObject("assembly");
        for(String field:assembly.keySet())assembly.addProperty(field,"pending".equals(field)?16:9007199254740991L);
        for(String field:new String[]{"pending","queued","written","received"}){
            JsonObject point=value.getAsJsonObject(field);
            point.addProperty("sender",4294967295L);point.addProperty("message",4294967295L);
            point.addProperty("total",8);point.addProperty("mask",255);
            point.addProperty("data_known",true);point.addProperty("data_sequence",9007199254740991L);
        }
        return value;
    }
    @Test public void largestAllowedValuesSurvive(){
        assertEquals(largestFixture(),RestrictedDelivery.project(largestFixture()));
    }
    @Test public void zeroUnknownAndNumericPrivacy(){
        JsonObject source=fixture();source.addProperty("payload","PRIVATE KEY secret");
        source.getAsJsonObject("flow").addProperty("destination","https://secret");
        JsonObject safe=RestrictedDelivery.project(source);
        assertEquals(0,safe.getAsJsonObject("flow").get("send_base").getAsLong());
        assertEquals(254,safe.getAsJsonObject("flow").get("ack_mask").getAsLong());
        assertFalse(safe.getAsJsonObject("pending").get("data_known").getAsBoolean());
        assertFalse(safe.toString().contains("secret"));
        source.getAsJsonObject("flow").addProperty("send_next",33);
        source.getAsJsonObject("pending").addProperty("data_sequence",1);
        safe=RestrictedDelivery.project(source);assertFalse(safe.has("flow"));assertFalse(safe.has("pending"));
        source=fixture();source.getAsJsonObject("flow").addProperty("pending",1.5);
        source.getAsJsonObject("queued").addProperty("data_known","false");
        source.getAsJsonObject("written").addProperty("mask",8);
        source.getAsJsonObject("received").addProperty("message",4294967296L);
        source.getAsJsonObject("assembly").addProperty("rtp",9007199254740992L);
        safe=RestrictedDelivery.project(source);
        assertEquals(1,safe.size());assertTrue(safe.has("pending"));
    }
    @Test public void traceDetailBoundKeepsFirstFailure(){
        JsonObject snapshot=RestrictedTraceTest.snapshot(192);
        for(JsonElement event:snapshot.getAsJsonArray("trace"))event.getAsJsonObject().add("delivery",fixture());
        snapshot.getAsJsonObject("first_failure").add("delivery",fixture());
        JsonObject safe=RestrictedTrace.project(snapshot,RestrictedTraceTest.TAG);
        int retained=0;
        for(JsonElement event:safe.getAsJsonArray("trace"))if(event.getAsJsonObject().has("delivery"))retained++;
        assertEquals(8,retained);assertEquals(184,safe.get("delivery_projection_dropped").getAsInt());
        assertTrue(safe.getAsJsonObject("first_failure").has("delivery"));
    }
}
