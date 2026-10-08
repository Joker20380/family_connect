package com.familyconnect.app;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.Test;
import static org.junit.Assert.*;

public class StartupResultTest {
    private JsonObject record() {
        return JsonParser.parseString("{\"schema\":1,\"attempt\":2,\"started_unix_ms\":10,\"observed_ms\":3,\"completed_ms\":4,\"complete\":true,\"stage\":\"HELLO_RECEIVE\",\"cause\":\"DEADLINE\",\"status\":\"FAILED\"}").getAsJsonObject();
    }

    @Test public void safeTypedCauseRetainsAttemptAndOrder() throws Exception {
        StartupResult result=new StartupResult(record().toString());
        assertEquals(2,result.attempt);assertEquals("HELLO_RECEIVE",result.stage);assertEquals("DEADLINE",result.cause);
        assertTrue(result.complete);assertTrue(result.failure() instanceof StartupResult.Failure);
        assertEquals(3,JsonParser.parseString(result.json).getAsJsonObject().get("observed_ms").getAsLong());
        assertEquals(4,JsonParser.parseString(result.json).getAsJsonObject().get("completed_ms").getAsLong());
    }

    @Test public void unknownCodesAndPrivateFieldsNeverEscape() throws Exception {
        JsonObject input=record();input.addProperty("stage","PRIVATE_TOKEN");input.addProperty("cause","https://secret/SDP");input.addProperty("exception","PASSWORD");input.addProperty("credentials","KEY");
        StartupResult result=new StartupResult(input.toString());
        assertEquals("UNKNOWN",result.stage);assertEquals("UNKNOWN",result.cause);
        for(String forbidden:new String[]{"PRIVATE","https://","SDP","PASSWORD","KEY","exception","credentials"})assertFalse(result.json.contains(forbidden));
        assertEquals("UNKNOWN:UNKNOWN",result.failure().getMessage());
    }

    @Test public void successHasNoFailureAndCancellationIsExplicit() throws Exception {
        JsonObject input=record();input.addProperty("status","SUCCEEDED");input.addProperty("cause","NONE");
        assertNull(new StartupResult(input.toString()).failure());
        input.addProperty("status","CANCELLED");input.addProperty("cause","CANCELLED");
        StartupResult cancelled=new StartupResult(input.toString());
        assertEquals("CANCELLED",((StartupResult.Failure)cancelled.failure()).result.cause);
    }

    @Test public void incompatibleSchemaIsNotAbsence() throws Exception {
        JsonObject input=record();input.addProperty("schema",2);
        try{new StartupResult(input.toString());fail("unsupported schema accepted");}catch(IllegalArgumentException expected){}
        input=record();input.addProperty("attempt",0);
        try{new StartupResult(input.toString());fail("unbound attempt accepted");}catch(IllegalArgumentException expected){}
    }
}
