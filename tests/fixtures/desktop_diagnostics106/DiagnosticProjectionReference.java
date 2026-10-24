package com.familyconnect.app;

import com.google.gson.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public final class DiagnosticProjectionReference {
    public static void main(String[] arguments) {
        JsonObject input=JsonParser.parseReader(new InputStreamReader(System.in,StandardCharsets.UTF_8)).getAsJsonObject();
        JsonObject output=new JsonObject();
        for(Map.Entry<String,JsonElement> entry:input.entrySet()) {
            JsonObject value=entry.getValue().getAsJsonObject(),source=value.getAsJsonObject("session"),session=new JsonObject(),result=new JsonObject();
            SpeedReceipt.project(source,session);
            JsonObject trace=RestrictedTrace.project(source.get("lifecycle"),RestrictedTrace.text(source,"session_tag"));
            if(trace!=null)session.add("lifecycle",trace);
            MuxLifecycle.project(source,session);
            JsonObject startup=RestrictedStartup.project(value.get("startup"));
            result.add("session",session);result.add("startup",startup==null?new JsonObject():startup);
            output.add(entry.getKey(),result);
        }
        System.out.println(output);
    }
}
