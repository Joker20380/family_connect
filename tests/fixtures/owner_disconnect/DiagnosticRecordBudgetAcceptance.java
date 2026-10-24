package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class DiagnosticRecordBudgetAcceptance {
    public static void main(String[] arguments)throws Exception{
        byte[] original=Files.readAllBytes(Path.of(arguments[0]));
        JsonObject ring=JsonParser.parseString(new String(original,StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("ring");
        JsonObject session=ring.getAsJsonObject("restricted_session");
        JsonArray incidents=session.getAsJsonObject("mux_lifecycle").getAsJsonArray("incidents");
        incidents.add(incidents.get(0).deepCopy());incidents.add(incidents.get(0).deepCopy());
        JsonObject projected=new JsonObject();MuxLifecycle.project(session,projected);
        session.add("mux_lifecycle",projected.get("mux_lifecycle"));
        int expanded=DiagnosticRecordBudget.size(ring);
        if(expanded!=262837)throw new AssertionError("Unexpected replay fixture");
        String current=session.toString(),events=ring.get("events").toString();
        DiagnosticRecordBudget.apply(ring);
        int bounded=DiagnosticRecordBudget.size(ring);
        if(bounded>DiagnosticRing.RECORD_LIMIT)throw new AssertionError("Unbounded snapshot");
        if(!current.equals(session.toString())||!events.equals(ring.get("events").toString()))throw new AssertionError("Current data changed");
        if(ring.getAsJsonArray("restricted_history").size()!=4)throw new AssertionError("History lost");
        JsonObject bundle=new JsonObject();byte[] encoded=ring.toString().getBytes(StandardCharsets.UTF_8);
        DiagnosticRing.exportRecord(bundle,"ring",encoded,ring.get("device_support_id").getAsString());
        DiagnosticRing.exportBytes(bundle);
        if(!java.util.Arrays.equals(original,Files.readAllBytes(Path.of(arguments[0]))))throw new AssertionError("Original changed");
        JsonObject receipt=new JsonObject();receipt.addProperty("result","BOUNDED_EXPORT_PASS");
        receipt.addProperty("expanded_bytes",expanded);receipt.addProperty("bounded_bytes",bounded);
        receipt.addProperty("current_session_unchanged",true);receipt.addProperty("events_unchanged",true);
        receipt.add("record_budget",ring.get("record_budget"));System.out.println(receipt);
    }
}
