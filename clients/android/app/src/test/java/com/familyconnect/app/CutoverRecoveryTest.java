package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;
import static org.junit.Assert.*;
import static com.familyconnect.app.ConnectivityOrchestrator.*;

public class CutoverRecoveryTest {
    private static JsonObject startup(long attempt) {
        JsonObject result=new JsonObject();
        result.addProperty("schema",1);result.addProperty("attempt",attempt);
        result.addProperty("started_unix_ms",1000);result.addProperty("complete",true);
        result.addProperty("status","FAILED");result.addProperty("stage","SEED_ADMISSION");
        result.addProperty("cause","DEADLINE");
        JsonObject observation=new JsonObject();observation.addProperty("point","STARTUP_CALLER");
        observation.addProperty("error_category","DEADLINE");observation.addProperty("context_state","DEADLINE");
        observation.addProperty("stop_at_observation","NONE");observation.addProperty("elapsed_ms",30000);
        result.add("observation",observation);
        JsonObject cleanup=new JsonObject();cleanup.addProperty("source","CLEANUP");cleanup.addProperty("elapsed_ms",30001);
        result.add("local_stop",cleanup);
        return result;
    }
    private static boolean retryable(JsonObject result) {
        JsonObject snapshot=new JsonObject();snapshot.add("owner_startup",result);
        return RestrictedRecovery.bootstrapRetryable(2,3,false,false,snapshot.toString());
    }
    private static byte[] response(long issued) {
        return ReadinessProductTest.response(issued,10000);
    }
    private static final class Fixture implements Host {
        long time,issued=1000;
        int active,opens,nativeStarts,releases;
        boolean unavailable,seedDeadline,cleanupFailure;
        Exception fetchFailure;
        Rejected forced;
        final List<Long> selected=new ArrayList<>();
        final ReadinessProductTest.Memory storage=new ReadinessProductTest.Memory();
        final RestrictedCache cache=ReadinessProductTest.cache(storage);
        final ReadinessProduct product=new ReadinessProduct(cache,new ReadinessProductTest.Memory(),"fixture",84,()->1500);
        final ConnectivityOrchestrator core=new ConnectivityOrchestrator(this);
        public long now(){return time;}
        public void pause(long millis){time+=millis;}
        public void open(String candidate,long deadline)throws Exception {
            assertEquals(RESTRICTED,candidate);assertEquals(0,active);opens++;
            assertTrue(deadline-time<=RESTRICTED_TIMEOUT_MS);
            if(forced!=null)throw forced;
            OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
            RestrictedBootstrap.Selection selection=RestrictedBootstrap.refresh(cache,product,receipt,()->{
                if(fetchFailure!=null)throw fetchFailure;
                if(unavailable)throw new SocketTimeoutException();
                receipt.challengeIssued();receipt.fetchAuthorized();
                return response(issued);
            },this,()->1500);
            if(selection.authorizationRejected)throw new Rejected(Failure.AUTH);
            byte[] raw=RestrictedBootstrap.select(selection.response,selection.availabilityFailure,core.state()==State.RESTORING);
            if(raw==null)throw new Rejected(Failure.BOOTSTRAP_UNAVAILABLE);
            selected.add(ControlJson.parse(raw).getAsJsonObject().get("issued_at").getAsLong());
            Arrays.fill(raw,(byte)0);active++;nativeStarts++;
            if(seedDeadline){time+=30000;throw new Rejected(Failure.BOOTSTRAP_UNAVAILABLE,retryable(startup(2)));}
        }
        public void closeCandidate(){if(cleanupFailure)throw new IllegalStateException();active=0;}
        public void release(){releases++;}
        public void remember(String candidate){fail();}
        public void event(Event event){}
        void connect(){core.connect(List.of(),null,null);if(!unavailable)assertEquals(State.CONNECTED,core.state());}
        void advance(long delay){time+=delay;core.retryIfDue();}
        long count(String event){return core.events().stream().filter(value->event.equals(value.name)).count();}
    }
    @Test public void refreshOutageDoesNotRestartOldRuntimeAndNextRefreshRecovers() {
        Fixture fixture=new Fixture();fixture.connect();fixture.unavailable=true;
        fixture.core.lost(Failure.NETWORK);
        assertEquals(State.RESTORING,fixture.core.state());assertEquals(1,fixture.nativeStarts);
        assertEquals(0,fixture.active);assertEquals(0,fixture.releases);
        fixture.advance(RECOVERY_BACKOFF_MS-1);assertEquals(2,fixture.opens);
        fixture.unavailable=false;fixture.issued=1200;fixture.advance(1);
        assertEquals(State.CONNECTED,fixture.core.state());assertEquals(List.of(1000L,1200L),fixture.selected);
        assertEquals(1,fixture.count("restoration_succeeded"));assertEquals(1,fixture.active);
        fixture.advance(MAX_RECOVERY_BACKOFF_MS);assertEquals(3,fixture.opens);
        assertEquals(Failure.NETWORK,fixture.core.events().stream().filter(event->event.name.equals("transport_lost")).findFirst().get().failure);
    }
    @Test public void stillPublishedOldDirectorySeedDeadlineGetsBoundedFreshRetry() {
        Fixture fixture=new Fixture();fixture.connect();fixture.seedDeadline=true;
        fixture.core.lost(Failure.NETWORK);assertEquals(State.RESTORING,fixture.core.state());
        assertEquals(List.of(1000L,1000L),fixture.selected);
        fixture.seedDeadline=false;fixture.issued=1300;fixture.advance(RECOVERY_BACKOFF_MS);
        assertEquals(State.CONNECTED,fixture.core.state());assertEquals(List.of(1000L,1000L,1300L),fixture.selected);
        assertTrue(fixture.core.events().stream().anyMatch(event->event.name.equals("candidate_failed")&&event.failure==Failure.BOOTSTRAP_UNAVAILABLE));
    }
    @Test public void bootstrapRecoveryCoolsDownAfterTwoDelayedSeries() {
        Fixture fixture=new Fixture();fixture.connect();fixture.unavailable=true;fixture.core.lost(Failure.NETWORK);
        fixture.advance(30000);assertEquals(State.RESTORING,fixture.core.state());
        fixture.advance(59999);assertEquals(3,fixture.opens);
        fixture.advance(1);assertEquals(State.RESTORING,fixture.core.state());assertEquals(4,fixture.opens);
        fixture.advance(RECOVERY_COOLDOWN_MS-1);assertEquals(4,fixture.opens);
        fixture.unavailable=false;fixture.advance(1);assertEquals(State.CONNECTED,fixture.core.state());
        assertEquals(5,fixture.opens);assertEquals(3,fixture.count("recovery_wait"));
        assertEquals(1,fixture.active);assertEquals(0,fixture.releases);
    }
    @Test public void briefRecoveryDoesNotResetItsBootstrapBudget() {
        Fixture fixture=new Fixture();fixture.connect();fixture.unavailable=true;fixture.core.lost(Failure.NETWORK);
        fixture.unavailable=false;fixture.advance(30000);assertEquals(State.CONNECTED,fixture.core.state());
        fixture.unavailable=true;fixture.core.lost(Failure.NETWORK);fixture.advance(30000);
        assertEquals(State.RESTORING,fixture.core.state());fixture.advance(60000);
        assertEquals(State.RESTORING,fixture.core.state());fixture.advance(120000);
        assertEquals(State.RESTORING,fixture.core.state());
        fixture.core.disconnect();assertEquals(0,fixture.active);
    }
    @Test public void initialRequestedConnectRetriesOnlyAfterBackoff() {
        Fixture fixture=new Fixture();fixture.unavailable=true;fixture.connect();
        assertEquals(State.RESTORING,fixture.core.state());fixture.advance(29999);
        assertEquals(1,fixture.opens);assertEquals(1,fixture.count("recovery_wait"));
        fixture.unavailable=false;fixture.advance(1);assertEquals(State.CONNECTED,fixture.core.state());
    }
    @Test public void unknownBootstrapAndSecurityFailuresRemainTerminal() {
        for(Failure failure:List.of(Failure.AUTH,Failure.CONFIGURATION,Failure.INTERNAL,Failure.BOOTSTRAP_UNAVAILABLE)){
            Fixture fixture=new Fixture();fixture.connect();fixture.forced=new Rejected(failure);
            fixture.core.lost(Failure.NETWORK);assertEquals(State.FAILED,fixture.core.state());
            fixture.advance(120000);assertEquals(2,fixture.opens);
        }
        assertFalse(new Rejected(Failure.AUTH,true).temporaryBootstrap);
    }
    @Test public void authAndCancelDuringWaitPreventAnyNewOpen() {
        for(Failure reason:List.of(Failure.AUTH,Failure.CANCELLED)){
            Fixture fixture=new Fixture();fixture.connect();fixture.unavailable=true;fixture.core.lost(Failure.NETWORK);
            fixture.core.interrupt(reason);fixture.advance(30000);
            assertEquals(reason==Failure.AUTH?State.FAILED:State.DISCONNECTED,fixture.core.state());
            assertEquals(2,fixture.opens);assertEquals(reason==Failure.AUTH?0:1,fixture.releases);
            fixture.advance(120000);assertEquals(2,fixture.opens);
        }
    }
    @Test public void disconnectAndCleanupFailureNeverStartAnotherCandidate() {
        Fixture fixture=new Fixture();fixture.connect();fixture.unavailable=true;fixture.core.lost(Failure.NETWORK);
        fixture.core.disconnect();fixture.advance(30000);assertEquals(2,fixture.opens);assertEquals(1,fixture.releases);
        fixture=new Fixture();fixture.connect();fixture.cleanupFailure=true;fixture.core.lost(Failure.NETWORK);
        fixture.advance(120000);assertEquals(State.FAILED,fixture.core.state());assertEquals(1,fixture.opens);
    }
    @Test public void rejectedChallengeTrustAndStaleImportNeverGainRetries() {
        for(Exception failure:List.of(new FriendsReadinessProtocol.AuthorizationFailure(),new javax.net.ssl.SSLHandshakeException("fixture"),
                new FriendsReadinessProtocol.ChallengeFailure(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_INCOMPATIBLE_RESPONSE))){
            Fixture fixture=new Fixture();fixture.connect();fixture.fetchFailure=failure;
            fixture.core.lost(Failure.NETWORK);assertEquals(State.FAILED,fixture.core.state());assertEquals(0,fixture.count("recovery_wait"));
        }
        Fixture stale=new Fixture();stale.connect();stale.issued=999;stale.core.lost(Failure.NETWORK);
        assertEquals(State.FAILED,stale.core.state());assertEquals(1,stale.nativeStarts);
    }
    @Test public void normalWarmStartCacheAndOtherConsumerRemainUnmodified()throws Exception {
        byte[] cached=response(1000),before=cached.clone();
        assertArrayEquals(cached,RestrictedBootstrap.select(cached,true,false));
        try{RestrictedBootstrap.select(cached,true,true);fail();}catch(Rejected failure){assertTrue(failure.temporaryBootstrap);}
        assertArrayEquals(before,cached);assertArrayEquals(before,RestrictedBootstrap.select(cached,true,false));
        assertArrayEquals(before,RestrictedBootstrap.select(cached,false,true));
    }
    @Test public void unavailableRefreshOnlyExpiredCacheRemainsRefreshable()throws Exception {
        Fixture revoked=new Fixture();revoked.connect();revoked.cache.denied();revoked.unavailable=true;
        revoked.core.lost(Failure.NETWORK);assertEquals(State.FAILED,revoked.core.state());assertEquals(0,revoked.count("recovery_wait"));
        for(boolean expired:new boolean[]{false,true}){
            ReadinessProductTest.Memory storage=new ReadinessProductTest.Memory();
            boolean[] valid={true};
            RestrictedCache cache=RestrictedCache.detailed(storage,raw->valid[0]?ReadinessImportResult.Code.READY:ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED);
            cache.importProduct(response(1000),new OwnerPrewarmReceipt(),1500);valid[0]=expired;
            ReadinessProduct product=new ReadinessProduct(cache,new ReadinessProductTest.Memory(),"fixture",84,()->1500);
            RestrictedBootstrap.Selection selected=RestrictedBootstrap.refresh(cache,product,new OwnerPrewarmReceipt(),()->{throw new SocketTimeoutException();},this,()->expired?10000:1500);
            assertEquals(expired,selected.availabilityFailure);assertNull(selected.response);
        }
    }
    @Test public void onlyMatchingCompletedPreLeaseDeadlineIsEligible() {
        assertTrue(retryable(startup(2)));assertFalse(retryable(startup(1)));
        for(String stage:List.of("HELLO_RECEIVE","FAMILY_AUTH","DIRECTORY","DEDICATED_AUTH","UNKNOWN")){
            JsonObject result=startup(2);result.addProperty("stage",stage);assertFalse(stage,retryable(result));
        }
        for(String cause:List.of("UNKNOWN","CANCELLED","CERTIFICATE_TIME_INVALID","CREDENTIALS_REJECTED","PROTOCOL_REJECTED")){
            JsonObject result=startup(2);result.addProperty("cause",cause);assertFalse(cause,retryable(result));
        }
        JsonObject result=startup(2);result.addProperty("cause","IO_DEADLINE");result.getAsJsonObject("observation").addProperty("error_category","IO_DEADLINE");assertTrue(retryable(result));
        result.addProperty("complete",false);assertFalse(retryable(result));
        for(String status:List.of("SUCCEEDED","RUNNING","CANCELLED")){
            result=startup(2);result.addProperty("status",status);assertFalse(retryable(result));
        }
        for(String stop:List.of("CLEANUP","CONNECT_CANCEL","STARTUP_BUDGET")){
            result=startup(2);JsonObject stopped=new JsonObject();stopped.addProperty("source",stop);result.add("local_stop",stopped);assertFalse(retryable(result));
        }
    }
    @Test public void firstDeadlineSurvivesLaterCleanupButNotPriorLocalStop() {
        JsonObject result=startup(2);String original=result.toString();
        assertTrue(retryable(result));assertEquals(original,result.toString());
        result.getAsJsonObject("observation").addProperty("context_state","LIVE");assertTrue(retryable(result));
        result.remove("local_stop");assertTrue(retryable(result));
        result=startup(2);result.getAsJsonObject("local_stop").addProperty("elapsed_ms",29999);assertFalse(retryable(result));
        for(String stop:List.of("CONNECT_CANCEL","STARTUP_BUDGET","CLEANUP")){
            result=startup(2);result.getAsJsonObject("observation").addProperty("stop_at_observation",stop);assertFalse(retryable(result));
        }
        result=startup(2);result.remove("observation");assertFalse(retryable(result));
        result=startup(2);result.getAsJsonObject("observation").addProperty("context_state","CANCELLED");assertFalse(retryable(result));
    }
    @Test public void phaseCancellationDenialAndMalformedEvidenceFailClosed() {
        JsonObject snapshot=new JsonObject();snapshot.add("owner_startup",startup(2));String raw=snapshot.toString();
        for(int phase:new int[]{-1,0,1,2,4,5})assertFalse(RestrictedRecovery.bootstrapRetryable(2,phase,false,false,raw));
        assertFalse(RestrictedRecovery.bootstrapRetryable(2,3,true,false,raw));
        assertFalse(RestrictedRecovery.bootstrapRetryable(2,3,false,true,raw));
        for(String invalid:new String[]{null,"", "{}", "null", "[]", "{"})assertFalse(RestrictedRecovery.bootstrapRetryable(2,3,false,false,invalid));
        assertEquals(raw,snapshot.toString());
    }
}
