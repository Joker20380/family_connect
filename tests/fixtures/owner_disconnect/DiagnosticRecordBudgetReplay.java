package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class DiagnosticRecordBudgetReplay {
    public static void main(String[] arguments) throws Exception {
        JsonObject bundle=JsonParser.parseString(Files.readString(Path.of(arguments[0]))).getAsJsonObject();
        JsonObject ring=bundle.getAsJsonObject("ring").deepCopy();
        byte[] original=ring.toString().getBytes(StandardCharsets.UTF_8);
        String support=ring.get("device_support_id").getAsString();
        DiagnosticRing.exportRecord(new JsonObject(),"ring",original,support);
        DiagnosticRing.exportBytes(bundle);
        JsonObject session=ring.getAsJsonObject("restricted_session");
        JsonArray incidents=session.getAsJsonObject("mux_lifecycle").getAsJsonArray("incidents");
        int before=incidents.size();
        if(before<1||before+2>32)throw new AssertionError("Fixture needs two available incident slots");
        incidents.add(incidents.get(0).deepCopy());
        incidents.add(incidents.get(0).deepCopy());
        JsonObject projected=new JsonObject();
        MuxLifecycle.project(session,projected);
        JsonObject lifecycle=projected.getAsJsonObject("mux_lifecycle");
        if(lifecycle.getAsJsonArray("incidents").size()!=before+2||lifecycle.has("projection_overflow"))
            throw new AssertionError("Component budget exceeded instead of record budget");
        session.add("mux_lifecycle",lifecycle);
        byte[] expanded=ring.toString().getBytes(StandardCharsets.UTF_8);
        if(expanded.length<=DiagnosticRing.RECORD_LIMIT)throw new AssertionError("Expected global record overflow");
        boolean rejected=false;
        try{DiagnosticRing.exportRecord(new JsonObject(),"ring",expanded,support);}
        catch(IOException failure){
            if(!"Diagnostic bound".equals(failure.getMessage()))throw failure;
            rejected=true;
        }
        if(!rejected)throw new AssertionError("Expected current record guard to reject growth");
        JsonObject result=new JsonObject();
        result.addProperty("result","REPRODUCED_RECORD_OVERFLOW_WITHIN_COMPONENT_BUDGET");
        result.addProperty("baseline_bytes",original.length);
        result.addProperty("expanded_bytes",expanded.length);
        result.addProperty("record_limit",DiagnosticRing.RECORD_LIMIT);
        result.addProperty("incidents_before",before);
        result.addProperty("incidents_after",incidents.size());
        result.addProperty("synthetic_added_contexts",2);
        result.addProperty("live_phone_memory_read",false);
        result.addProperty("original_export_unmodified",true);
        System.out.println(result);
    }
}
