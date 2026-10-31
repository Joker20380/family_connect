package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.util.List;
import org.junit.Test;
import static org.junit.Assert.*;
import static com.familyconnect.app.ConnectivityOrchestrator.*;

public class NightRecoveryTest {
    static JsonObject websocket() {
        JsonObject snapshot=RestrictedRecoveryTest.snapshot();
        JsonObject diagnostic=snapshot.getAsJsonObject("packet").getAsJsonObject("diagnostic");
        diagnostic.addProperty("reliable_terminal","carrier_closed");
        JsonObject lifecycle=diagnostic.getAsJsonObject("lifecycle"),first=lifecycle.getAsJsonObject("first_failure");
        first.addProperty("stage","WEBSOCKET");first.addProperty("state","CLOSED");
        first.addProperty("reason","SIGNAL_WS_CLOSE");first.addProperty("close_reason","READ_ERROR");
        JsonObject close=first.deepCopy();close.addProperty("stage","CARRIER");close.addProperty("reason","CARRIER_ERROR");close.addProperty("close_source","SIGNAL_READ");
        lifecycle.add("first_close",close);return snapshot;
    }
    @Test public void observedNightWebsocketCloseIsTemporaryNotInternal() {
        assertEquals(Failure.NETWORK,RestrictedRecovery.failure(3,false,false,websocket().toString()));
    }
    @Test public void policyAndProtocolClosureDoNotBecomeNetwork() {
        JsonObject snapshot=websocket(),diagnostic=snapshot.getAsJsonObject("packet").getAsJsonObject("diagnostic");
        JsonObject first=diagnostic.getAsJsonObject("lifecycle").getAsJsonObject("first_failure");
        first.addProperty("close_code",1008);
        assertEquals(Failure.INTERNAL,RestrictedRecovery.failure(3,false,false,snapshot.toString()));
        first.remove("close_code");diagnostic.addProperty("terminal_reason","MUX_PROTOCOL");
        assertEquals(Failure.INTERNAL,RestrictedRecovery.failure(3,false,false,snapshot.toString()));
        assertEquals(Failure.AUTH,RestrictedRecovery.failure(3,false,true,websocket().toString()));
        assertEquals(Failure.CANCELLED,RestrictedRecovery.failure(3,true,false,websocket().toString()));
    }
    static final class Fixture implements Host {
        long time;int opens,active,peak,releases;boolean network=true;
        Failure failure;boolean temporary;ConnectivityOrchestrator core=new ConnectivityOrchestrator(this);
        public long now(){return time;}
        public boolean networkAvailable(){return network;}
        public void pause(long millis){time+=millis;}
        public void open(String candidate,long deadline)throws Exception{assertEquals(0,active);active++;peak=Math.max(peak,active);opens++;if(failure!=null)throw new Rejected(failure,temporary);}
        public void closeCandidate(){active=0;}
        public void release(){releases++;}
        public void remember(String candidate){}
        public void event(Event event){}
        void connect(boolean auto){core.connect(auto?List.of("awg"):List.of(),null,null);}
        void stable(){core.trafficHealthy(true);time+=STABLE_TRAFFIC_MS;core.trafficHealthy(true);}
    }
    @Test public void threeIndependentStableRecoveriesWorkInBothModes() {
        for(boolean auto:new boolean[]{false,true}){
            Fixture fixture=new Fixture();fixture.connect(auto);
            for(int index=0;index<3;index++){
                fixture.stable();fixture.core.lost(Failure.NETWORK);
                assertEquals(State.CONNECTED,fixture.core.state());assertEquals(index+2,fixture.opens);
            }
            assertEquals(1,fixture.peak);assertEquals(0,fixture.releases);
            fixture.core.disconnect();assertEquals(0,fixture.active);assertEquals(1,fixture.releases);
        }
    }
    @Test public void exhaustedBootstrapBurstCoolsDownThenRecoversWithoutNewConnect() {
        Fixture fixture=new Fixture();fixture.connect(false);
        fixture.failure=Failure.BOOTSTRAP_UNAVAILABLE;fixture.temporary=true;fixture.core.lost(Failure.NETWORK);
        fixture.time+=RECOVERY_BACKOFF_MS;fixture.core.retryIfDue();
        fixture.time+=RECOVERY_BACKOFF_MS*2;fixture.core.retryIfDue();
        assertEquals(State.RESTORING,fixture.core.state());int opens=fixture.opens;
        fixture.time+=RECOVERY_COOLDOWN_MS-1;fixture.core.retryIfDue();assertEquals(opens,fixture.opens);
        fixture.failure=null;fixture.time++;fixture.core.retryIfDue();assertEquals(State.CONNECTED,fixture.core.state());
        assertEquals(1,fixture.peak);
    }
    @Test public void missingNetworkDoesNotCreateRoomsAndLaterResumes() {
        Fixture fixture=new Fixture();fixture.connect(false);fixture.network=false;fixture.core.lost(Failure.NETWORK);
        assertEquals(1,fixture.opens);assertEquals(0,fixture.active);assertEquals(State.RESTORING,fixture.core.state());
        fixture.time+=RECOVERY_BACKOFF_MS;fixture.core.retryIfDue();assertEquals(1,fixture.opens);
        fixture.network=true;fixture.time+=MAX_RECOVERY_BACKOFF_MS;fixture.core.retryIfDue();
        assertEquals(State.CONNECTED,fixture.core.state());assertEquals(2,fixture.opens);
    }
    @Test public void shortConnectedDoesNotResetBackoffOrRecoveryBurst() {
        Fixture fixture=new Fixture();fixture.connect(false);fixture.failure=Failure.NETWORK;fixture.core.lost(Failure.NETWORK);
        fixture.time+=RECOVERY_BACKOFF_MS;fixture.failure=null;fixture.core.retryIfDue();
        fixture.core.trafficHealthy(true);fixture.time+=1000;fixture.core.trafficHealthy(false);fixture.core.lost(Failure.NETWORK);
        int opens=fixture.opens;fixture.time+=RECOVERY_BACKOFF_MS;fixture.core.retryIfDue();assertEquals(opens,fixture.opens);
        fixture.time+=RECOVERY_BACKOFF_MS;fixture.core.retryIfDue();assertEquals(opens+1,fixture.opens);
    }
    @Test public void explicitDisconnectAndRevokeStopCooldown() {
        for(Failure reason:new Failure[]{Failure.CANCELLED,Failure.AUTH}){
            Fixture fixture=new Fixture();fixture.connect(false);fixture.network=false;fixture.core.lost(Failure.NETWORK);
            fixture.core.interrupt(reason);fixture.time+=RECOVERY_COOLDOWN_MS;fixture.core.retryIfDue();
            fixture.network=true;fixture.time+=RECOVERY_COOLDOWN_MS;fixture.core.retryIfDue();assertEquals(1,fixture.opens);
            assertEquals(reason==Failure.AUTH?State.FAILED:State.DISCONNECTED,fixture.core.state());
        }
    }
    @Test public void delayedPollAfterSleepIsOneAttemptNotCatchupLoop() {
        Fixture fixture=new Fixture();fixture.connect(false);fixture.failure=Failure.NETWORK;fixture.core.lost(Failure.NETWORK);
        fixture.time+=12*60*60*1000L;int opens=fixture.opens;fixture.core.retryIfDue();
        for(int index=0;index<100;index++)fixture.core.retryIfDue();assertEquals(opens+1,fixture.opens);
    }
    @Test public void restartRestoresOnlyExplicitSupportedIntentWithVpnPermission() {
        for(String mode:new String[]{"telemost","auto"}){
            assertTrue(ConnectionResume.allowed(true,true,mode));
            assertFalse(ConnectionResume.allowed(false,true,mode));assertFalse(ConnectionResume.allowed(true,false,mode));
        }
        for(String mode:new String[]{null,"restricted","restricted-refresh","awg","tcp","invalid"})assertFalse(ConnectionResume.allowed(true,true,mode));
        Fixture replacement=new Fixture();assertEquals(State.DISCONNECTED,replacement.core.state());replacement.connect(false);
        assertEquals(State.CONNECTED,replacement.core.state());assertEquals(1,replacement.opens);
    }
}
