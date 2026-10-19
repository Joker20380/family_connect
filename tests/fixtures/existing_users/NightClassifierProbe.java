package com.familyconnect.app;

import com.google.gson.JsonObject;

public final class NightClassifierProbe {
    public static void main(String[] args) {
        JsonObject snapshot=RestrictedRecoveryTest.snapshot();
        JsonObject diagnostic=snapshot.getAsJsonObject("packet").getAsJsonObject("diagnostic");
        diagnostic.addProperty("reliable_terminal","carrier_closed");
        JsonObject lifecycle=diagnostic.getAsJsonObject("lifecycle"),first=lifecycle.getAsJsonObject("first_failure");
        first.addProperty("stage","WEBSOCKET");first.addProperty("state","CLOSED");
        first.addProperty("reason","SIGNAL_WS_CLOSE");first.addProperty("close_reason","READ_ERROR");
        JsonObject close=first.deepCopy();close.addProperty("stage","CARRIER");
        close.addProperty("reason","CARRIER_ERROR");close.addProperty("close_source","SIGNAL_READ");
        lifecycle.add("first_close",close);
        String actual=RestrictedRecovery.failure(3,false,false,snapshot.toString()).name();
        if(args.length!=1||!actual.equals(args[0]))throw new AssertionError(actual);
        System.out.println("OBSERVED_SHAPE_CLASSIFICATION="+actual);
    }
}
