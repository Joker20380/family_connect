package com.familyconnect.app;

import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessSummaryTest {
    @Test public void missingIsUnknownAndNotUsable() {
        String result=ReadinessSummary.restricted(new JsonObject());
        assertTrue(result.contains("cache: UNKNOWN"));
        assertTrue(result.contains("usable: false"));
    }
    @Test public void arbitraryDataCannotBecomeDiagnostics() {
        JsonObject value=new JsonObject();
        for(String name:new String[]{"cache","expired","restricted_provisioning","structurally_valid","seeds","remaining_seconds","usable","private_key","room"})value.addProperty(name,"private-sentinel-do-not-emit");
        String result=ReadinessSummary.restricted(value);
        assertFalse(result.contains("sentinel"));
        assertFalse(result.contains("private_key"));
        assertTrue(result.contains("usable: false"));
    }
    @Test public void boundedMetadataOnly() {
        JsonObject value=new JsonObject();value.addProperty("cache","PRESENT");value.addProperty("seeds",2);value.addProperty("remaining_seconds",600);value.addProperty("usable",true);
        String result=ReadinessSummary.restricted(value);
        assertTrue(result.contains("cache: PRESENT"));assertTrue(result.contains("seeds: 2"));assertTrue(result.contains("remaining_seconds: 600"));
        value.addProperty("remaining_seconds",Long.MAX_VALUE);
        assertTrue(ReadinessSummary.restricted(value).contains("remaining_seconds: -1"));
    }
}
