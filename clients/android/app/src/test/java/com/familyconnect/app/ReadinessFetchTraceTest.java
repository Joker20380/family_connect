package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessFetchTraceTest {
    @Test public void wrappedIoIsNotMisreportedAsProtocol(){
        ReadinessFetchTrace trace=new ReadinessFetchTrace(new OwnerPrewarmReceipt(),"",1);
        trace.failed(new java.io.IOException("private detail must not appear"));
        trace.failed(new FriendsReadinessProtocol.ChallengeFailure(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_TEMPORARY_SERVER_FAILURE,false));
        com.google.gson.JsonArray failures=trace.json().getAsJsonArray("failures");
        assertEquals("IO",failures.get(0).getAsJsonObject().get("error_class").getAsString());
        assertEquals("IO",failures.get(1).getAsJsonObject().get("error_class").getAsString());
        assertEquals("CHALLENGE_TEMPORARY_SERVER_FAILURE",failures.get(1).getAsJsonObject().get("challenge_code").getAsString());
        assertFalse(failures.get(1).getAsJsonObject().get("availability_failure").getAsBoolean());
        assertFalse(failures.toString().contains("private detail"));
    }
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
