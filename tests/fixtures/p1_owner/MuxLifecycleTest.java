package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class MuxLifecycleTest {
    @Test public void boundsAndPayloadExclusion(){
        JsonObject source=new JsonObject(),raw=new JsonObject();JsonArray events=new JsonArray();
        for(int index=0;index<1000;index++){JsonObject event=new JsonObject();event.addProperty("index",index);event.addProperty("stage","receive");event.addProperty("payload","private content");events.add(event);}
        raw.add("events",events);source.add("mux_lifecycle",raw);JsonObject safe=new JsonObject();MuxLifecycle.project(source,safe);
        JsonObject output=safe.getAsJsonObject("mux_lifecycle");assertEquals(32,output.getAsJsonArray("events").size());assertFalse(output.toString().contains("private"));assertTrue(output.toString().length()<8192);
    }
    @Test public void preservesUnknownAndDoesNotReclassify(){
        JsonObject source=JsonParser.parseString("{\"mux_lifecycle\":{\"first_unknown\":{\"known\":false,\"cancelled\":true,\"failure_at\":99,\"event\":{\"id\":7,\"kind\":4,\"stage\":\"unknown\"},\"stream\":{\"id\":0}}}}").getAsJsonObject();
        JsonObject safe=new JsonObject();safe.addProperty("protocol_errors",17);MuxLifecycle.project(source,safe);
        assertEquals(17,safe.get("protocol_errors").getAsInt());assertFalse(safe.getAsJsonObject("mux_lifecycle").getAsJsonObject("first_unknown").get("known").getAsBoolean());
    }
    @Test public void rejectsMalformedFields(){
        JsonObject source=JsonParser.parseString("{\"mux_lifecycle\":{\"failure_at\":-1,\"failure_reason\":\"secret\",\"events\":[null,5,{\"id\":-2,\"stage\":\"secret\",\"reason\":\"secret\"}]}}").getAsJsonObject();
        JsonObject safe=new JsonObject();MuxLifecycle.project(source,safe);String output=safe.toString();assertFalse(output.contains("secret"));assertFalse(output.contains("-1"));assertFalse(output.contains("-2"));
    }
    @Test public void absentObserverStaysAbsent(){
        JsonObject safe=new JsonObject();MuxLifecycle.project(new JsonObject(),safe);assertFalse(safe.has("mux_lifecycle"));
    }
}
