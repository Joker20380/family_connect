package com.familyconnect.app;

import com.google.gson.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public final class SupportProjectionReference {
    public static void main(String[] arguments) {
        JsonObject input=JsonParser.parseReader(new InputStreamReader(System.in,StandardCharsets.UTF_8)).getAsJsonObject();
        JsonObject output=new JsonObject();
        for(Map.Entry<String,JsonElement> entry:input.entrySet()) {
            JsonObject report=SupportSnapshot.project(entry.getValue().getAsJsonObject(),2011,1000000);
            report.addProperty("report_id","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
            output.add(entry.getKey(),report);
        }
        System.out.println(output);
    }
}
