package com.familyconnect.app;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.util.Collections;
import org.junit.Test;
import static org.junit.Assert.*;
import static com.familyconnect.app.ConnectivityOrchestrator.*;

public class AuthenticatedBootstrapRecoveryTest {
    private static final String TAG="a".repeat(64);
    private static JsonObject startup() {
        JsonObject value=new JsonObject();
        value.addProperty("schema",1);value.addProperty("attempt",4);
        value.addProperty("started_unix_ms",1000);value.addProperty("complete",true);
        value.addProperty("status","FAILED");value.addProperty("stage","HELLO_RECEIVE");
        value.addProperty("cause","CLOSED_PIPE");value.addProperty("bootstrap_exchanges_dropped",0);
        JsonObject observation=new JsonObject();observation.addProperty("point","FAMILY_RECEIVE");
        observation.addProperty("error_category","CLOSED_PIPE");observation.addProperty("context_state","LIVE");
        observation.addProperty("stop_at_observation","NONE");observation.addProperty("elapsed_ms",14939);
        observation.addProperty("bootstrap_exchange_tag",TAG);value.add("observation",observation);
        JsonObject exchange=new JsonObject();exchange.addProperty("bootstrap_exchange_tag",TAG);
        exchange.addProperty("family_authenticated",true);JsonArray exchanges=new JsonArray();exchanges.add(exchange);
        value.add("bootstrap_exchanges",exchanges);
        JsonObject cleanup=new JsonObject();cleanup.addProperty("source","CLEANUP");cleanup.addProperty("elapsed_ms",14944);
        value.add("local_stop",cleanup);return value;
    }
    private static String snapshot(JsonObject startup) {
        JsonObject value=new JsonObject();value.add("owner_startup",startup);return value.toString();
    }
    private static boolean recoverable(JsonObject value) {
        return RestrictedRecovery.bootstrapRetryable(4,3,false,false,snapshot(value));
    }
    @Test public void correlatedAuthenticatedHelloCloseIsEligibleForExistingBoundedRecovery() {
        assertTrue(recoverable(startup()));
    }
    @Test public void missingConflictingAndDroppedAuthenticationFactsAreNotRecoverable() {
        JsonObject value=startup();value.remove("bootstrap_exchanges");assertFalse(recoverable(value));
        value=startup();value.getAsJsonArray("bootstrap_exchanges").get(0).getAsJsonObject().addProperty("family_authenticated",false);assertFalse(recoverable(value));
        value=startup();value.getAsJsonArray("bootstrap_exchanges").get(0).getAsJsonObject().addProperty("bootstrap_exchange_tag","b".repeat(64));assertFalse(recoverable(value));
        value=startup();value.getAsJsonArray("bootstrap_exchanges").add(value.getAsJsonArray("bootstrap_exchanges").get(0).deepCopy());assertFalse(recoverable(value));
        value=startup();value.addProperty("bootstrap_exchanges_dropped",1);assertFalse(recoverable(value));
        value=startup();value.getAsJsonObject("observation").remove("bootstrap_exchange_tag");assertFalse(recoverable(value));
    }
    @Test public void securityProtocolTimeoutAndLaterExchangeFailuresStayTerminal() {
        for(String cause:new String[]{"CERTIFICATE_AUTHORITY","CERTIFICATE_INVALID","CREDENTIALS_REJECTED","PROTOCOL_REJECTED","DEADLINE","IO_DEADLINE","EOF","UNKNOWN"}) {
            JsonObject value=startup();value.addProperty("cause",cause);value.getAsJsonObject("observation").addProperty("error_category",cause);
            assertFalse(cause,recoverable(value));
        }
        for(String stage:new String[]{"FAMILY_AUTH","REQUEST_SEND","DESCRIPTOR_RECEIVE","DESCRIPTOR_VALIDATE","DEDICATED_AUTH"}) {
            JsonObject value=startup();value.addProperty("stage",stage);assertFalse(stage,recoverable(value));
        }
        String raw=snapshot(startup());
        assertFalse(RestrictedRecovery.bootstrapRetryable(4,3,false,true,raw));
        assertFalse(RestrictedRecovery.bootstrapRetryable(4,3,true,false,raw));
        assertFalse(RestrictedRecovery.bootstrapRetryable(5,3,false,false,raw));
        assertFalse(RestrictedRecovery.bootstrapRetryable(4,5,false,false,raw));
    }
    @Test public void cancellationCleanupAndContextMustNotBeReclassified() {
        for(String context:new String[]{"DEADLINE","CANCELLED","UNKNOWN"}) {
            JsonObject value=startup();value.getAsJsonObject("observation").addProperty("context_state",context);assertFalse(recoverable(value));
        }
        JsonObject value=startup();value.getAsJsonObject("observation").addProperty("point","STARTUP_CALLER");assertFalse(recoverable(value));
        value=startup();value.getAsJsonObject("observation").addProperty("stop_at_observation","CONNECT_CANCEL");assertFalse(recoverable(value));
        value=startup();value.getAsJsonObject("local_stop").addProperty("elapsed_ms",14938);assertFalse(recoverable(value));
        value=startup();value.addProperty("complete",false);assertFalse(recoverable(value));
    }
    private static final class ProbeHost implements Host {
        long time;int opens;boolean recovered;
        public long now(){return time;}
        public void pause(long millis){time+=millis;}
        public void open(String candidate,long deadline)throws Exception {
            opens++;if(opens>1&&!recovered)throw new Rejected(Failure.BOOTSTRAP_UNAVAILABLE,recoverable(startup()));
        }
        public void closeCandidate(){}
        public void release(){}
        public void remember(String candidate){}
        public void event(Event event){}
    }
    @Test public void recoveryWaitsAndCanSucceedWithoutNewConnect() {
        ProbeHost host=new ProbeHost();ConnectivityOrchestrator owner=new ConnectivityOrchestrator(host);
        owner.connect(Collections.emptyList(),null,null);assertEquals(State.CONNECTED,owner.state());
        owner.lost(Failure.NETWORK);assertEquals(State.RESTORING,owner.state());
        int opens=host.opens;owner.retryIfDue();assertEquals(opens,host.opens);
        host.recovered=true;host.time+=RECOVERY_BACKOFF_MS;owner.retryIfDue();
        assertEquals(State.CONNECTED,owner.state());assertEquals(opens+1,host.opens);
    }
    @Test public void persistentFailureCoolsDownAndCancelStopsRetry() {
        ProbeHost host=new ProbeHost();ConnectivityOrchestrator owner=new ConnectivityOrchestrator(host);
        owner.connect(Collections.emptyList(),null,null);owner.lost(Failure.NETWORK);
        for(int attempt=0;attempt<MAX_BOOTSTRAP_RECOVERIES;attempt++){host.time+=MAX_RECOVERY_BACKOFF_MS;owner.retryIfDue();}
        assertEquals(State.RESTORING,owner.state());assertEquals(2+MAX_BOOTSTRAP_RECOVERIES,host.opens);
        int waiting=host.opens;host.time+=RECOVERY_COOLDOWN_MS-1;owner.retryIfDue();assertEquals(waiting,host.opens);
        host=new ProbeHost();owner=new ConnectivityOrchestrator(host);
        owner.connect(Collections.emptyList(),null,null);owner.lost(Failure.NETWORK);
        int opens=host.opens;owner.interrupt(Failure.CANCELLED);host.time+=MAX_RECOVERY_BACKOFF_MS;owner.retryIfDue();
        assertEquals(State.DISCONNECTED,owner.state());assertEquals(opens,host.opens);
    }
}
