package com.familyconnect.app;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;
import static com.familyconnect.app.ConnectivityOrchestrator.Failure;

public class RestrictedRecoveryTest {
    private static final String TAG="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
    static JsonObject snapshot() {
        JsonObject first=new JsonObject();
        first.addProperty("session_tag",TAG);first.addProperty("sequence",21);first.addProperty("timestamp_ms",1791126430843L);
        first.addProperty("stage","CARRIER");first.addProperty("state","FAILED");first.addProperty("reason","RELIABLE_RETRY_EXHAUSTED");
        first.addProperty("reliable_retries",8);first.addProperty("reliable_pending",8);
        first.addProperty("reliable_ack_age_ms",428);first.addProperty("reliable_progress_age_ms",8155);
        JsonObject lifecycle=new JsonObject();lifecycle.addProperty("session_tag",TAG);lifecycle.addProperty("correlation_status","VALID");
        lifecycle.add("first_failure",first);lifecycle.add("trace",new JsonArray());
        JsonObject diagnostic=new JsonObject();diagnostic.addProperty("session_tag",TAG);diagnostic.addProperty("correlation_status","VALID");
        diagnostic.addProperty("terminal_reason","IO_CLOSED");diagnostic.addProperty("reliable_terminal","recovery_exhausted");
        diagnostic.add("lifecycle",lifecycle);
        JsonObject packet=new JsonObject();packet.add("diagnostic",diagnostic);
        JsonObject result=new JsonObject();result.add("packet",packet);return result;
    }
    private static JsonObject diagnostic(JsonObject snapshot){return snapshot.getAsJsonObject("packet").getAsJsonObject("diagnostic");}
    private static JsonObject first(JsonObject snapshot){return diagnostic(snapshot).getAsJsonObject("lifecycle").getAsJsonObject("first_failure");}
    private static Failure failure(JsonObject snapshot){return RestrictedRecovery.failure(3,false,false,snapshot.toString());}

    @Test public void onlyProvenRetryExhaustionIsRecoverable() {
        for(String terminal:new String[]{"IO_CLOSED","EOF","RELIABLE_EXHAUSTED"}) {
            JsonObject snapshot=snapshot();diagnostic(snapshot).addProperty("terminal_reason",terminal);
            assertEquals(Failure.NETWORK,failure(snapshot));
        }
        for(String reason:RestrictedTrace.REASONS.split("\\|")) {
            if(reason.equals("RELIABLE_RETRY_EXHAUSTED"))continue;
            JsonObject snapshot=snapshot();first(snapshot).addProperty("reason",reason);
            assertEquals(reason,Failure.INTERNAL,failure(snapshot));
        }
    }
    @Test public void authorityAndCancellationOverrideNetworkAndHealthyStates() {
        String snapshot=snapshot().toString();
        for(int phase:new int[]{-1,0,1,2,3,4,5}) {
            assertEquals(Failure.AUTH,RestrictedRecovery.failure(phase,false,true,snapshot));
            assertEquals(phase==5?Failure.AUTH:Failure.CANCELLED,RestrictedRecovery.failure(phase,true,false,snapshot));
        }
        assertEquals(Failure.AUTH,RestrictedRecovery.failure(3,true,true,snapshot));
        assertEquals(Failure.AUTH,RestrictedRecovery.failure(5,false,false,null));
        assertNull(RestrictedRecovery.failure(2,false,false,null));
        for(int phase:new int[]{-1,0,1,4})assertEquals(Failure.INTERNAL,RestrictedRecovery.failure(phase,false,false,snapshot));
    }
    @Test public void terminalSecurityAndProtocolFailuresCannotBeMaskedByTrace() {
        for(String terminal:new String[]{"FAMILY_REJECTED","CANCELLED","RELIABLE_PROTOCOL","MUX_PROTOCOL","UNKNOWN","REMOTE_RESET","DEADLINE",""}) {
            JsonObject snapshot=snapshot();diagnostic(snapshot).addProperty("terminal_reason",terminal);
            Failure expected=terminal.equals("FAMILY_REJECTED")?Failure.AUTH:terminal.equals("CANCELLED")?Failure.CANCELLED:Failure.INTERNAL;
            assertEquals(terminal,expected,failure(snapshot));
        }
        for(String terminal:new String[]{"closed","cancelled","protocol_violation","remote_reset","carrier_closed",""}) {
            JsonObject snapshot=snapshot();diagnostic(snapshot).addProperty("reliable_terminal",terminal);
            assertEquals(Failure.INTERNAL,failure(snapshot));
        }
    }
    @Test public void malformedMissingOrUncorrelatedEvidenceFailsClosed() {
        for(String raw:new String[]{null,"", "{", "null", "[]", "{}", "{\"packet\":{\"diagnostic\":null}}"})
            assertEquals(Failure.INTERNAL,RestrictedRecovery.failure(3,false,false,raw));
        for(String field:new String[]{"session_tag","correlation_status","lifecycle","terminal_reason","reliable_terminal"}) {
            JsonObject snapshot=snapshot();diagnostic(snapshot).remove(field);assertEquals(field,Failure.INTERNAL,failure(snapshot));
        }
        for(String field:new String[]{"session_tag","sequence","timestamp_ms","stage","state","reason"}) {
            JsonObject snapshot=snapshot();first(snapshot).remove(field);assertEquals(field,Failure.INTERNAL,failure(snapshot));
        }
        for(String field:new String[]{"session_tag","stage","state"}) {
            JsonObject snapshot=snapshot();first(snapshot).addProperty(field,field.equals("stage")?"FAMILY_TLS":field.equals("state")?"CLOSED":"0".repeat(64));
            assertEquals(Failure.INTERNAL,failure(snapshot));
        }
        JsonObject snapshot=snapshot();diagnostic(snapshot).getAsJsonObject("lifecycle").remove("first_failure");
        assertEquals(Failure.INTERNAL,failure(snapshot));
    }
    @Test public void laterFailuresNeverReplaceTheFirstCause() {
        JsonObject snapshot=snapshot();JsonObject lifecycle=diagnostic(snapshot).getAsJsonObject("lifecycle");
        JsonObject later=first(snapshot).deepCopy();later.addProperty("sequence",22);later.addProperty("stage","FAMILY_TLS");later.addProperty("reason","FAMILY_TLS_ERROR");
        lifecycle.getAsJsonArray("trace").add(later);assertEquals(Failure.NETWORK,failure(snapshot));
        later.addProperty("stage","CARRIER");later.addProperty("reason","RELIABLE_RETRY_EXHAUSTED");
        first(snapshot).addProperty("reason","UNKNOWN_INTERNAL");assertEquals(Failure.INTERNAL,failure(snapshot));
    }
}
