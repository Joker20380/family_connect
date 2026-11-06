package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessFetchTraceTest {
    @Test public void boundedStagesRetainBudgetAndFailureCategory(){
        ReadinessFetchTrace trace=new ReadinessFetchTrace(new OwnerPrewarmReceipt(),"",1);
        trace.budget(30000);
        trace.request("/friends/restricted-readiness",ReadinessFetchTrace.Route.PROVISIONING);
        for(int index=0;index<70;index++)trace.stage(ReadinessFetchTrace.Stage.CARRIER_REQUEST);
        trace.failed(new java.net.SocketTimeoutException("must not appear"));
        com.google.gson.JsonObject value=trace.json();
        assertEquals(64,value.getAsJsonArray("stages").size());
        long remaining=value.getAsJsonArray("stages").get(63).getAsJsonObject().get("remaining_ms").getAsLong();
        assertTrue(remaining>=0&&remaining<=30000);
        assertEquals("TIMEOUT",value.getAsJsonArray("failures").get(0).getAsJsonObject().get("error_class").getAsString());
        assertFalse(value.toString().contains("must not appear"));
    }
}
