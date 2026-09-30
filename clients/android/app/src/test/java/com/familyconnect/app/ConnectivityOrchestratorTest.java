package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import static com.familyconnect.app.ConnectivityOrchestrator.*;

public class ConnectivityOrchestratorTest {
    private static final class Fixture implements Host {
        long time;
        int active,peak,opens,releases;
        boolean guard=true,cleanupFailure;
        String hint,cancelCandidate,cancelPhase;
        final List<String> attempts=new ArrayList<>(),phases=new ArrayList<>();
        final Map<String,Failure> failures=new HashMap<>();
        final ConnectivityOrchestrator core=new ConnectivityOrchestrator(this);
        public long now(){return time;}
        public List<String> configure(List<String> configured,long deadline){guard=true;return configured;}
        public void pause(long millis){assertTrue(guard);time+=millis;}
        public void open(String candidate,long deadline)throws Exception{
            assertTrue(guard);assertEquals(0,active);active++;peak=Math.max(peak,active);opens++;attempts.add(candidate);
            for(String phase:RESTRICTED.equals(candidate)?new String[]{"bootstrap","broker","dedicated"}:new String[]{"normal"}){
                phases.add(phase);time+=10;
                if(candidate.equals(cancelCandidate)&&(cancelPhase==null||cancelPhase.equals(phase)))core.interrupt(Failure.CANCELLED);
                core.check(deadline);
            }
            Failure failure=failures.get(candidate);
            if(failure!=null)throw new Rejected(failure);
        }
        public void closeCandidate()throws Exception{assertTrue(guard);if(cleanupFailure)throw new IllegalStateException();active=0;}
        public void release(){guard=false;releases++;}
        public void remember(String candidate){hint=candidate;}
        public void event(Event event){}
        void connect(){core.connect(Arrays.asList("awg","tcp"),"awg",hint);}
        long count(String name){return core.events().stream().filter(event->event.name.equals(name)).count();}
    }
    @Test public void primaryNeverStartsBootstrap(){
        Fixture fixture=new Fixture();fixture.connect();assertEquals(State.CONNECTED,fixture.core.state());
        assertEquals(Arrays.asList("awg"),fixture.attempts);assertEquals("awg",fixture.hint);assertEquals(1,fixture.count("time_to_connected"));
    }
    @Test public void alternateNeverStartsBootstrap(){
        Fixture fixture=new Fixture();fixture.failures.put("awg",Failure.TRANSPORT_UNAVAILABLE);fixture.connect();
        assertEquals(Arrays.asList("awg","tcp"),fixture.attempts);assertEquals("tcp",fixture.hint);assertEquals(1,fixture.count("fallback"));
    }
    @Test public void exhaustedNormalInvokesFreshBootstrapAndDedicated(){
        Fixture fixture=new Fixture();fixture.failures.put("awg",Failure.NETWORK);fixture.failures.put("tcp",Failure.TRANSPORT_UNAVAILABLE);fixture.connect();
        assertEquals(State.CONNECTED,fixture.core.state());assertEquals(RESTRICTED,fixture.core.selected());assertNull(fixture.hint);
        assertEquals(Arrays.asList("normal","normal","bootstrap","broker","dedicated"),fixture.phases);assertEquals(1,fixture.peak);
    }
    @Test public void unavailableBootstrapIsBoundedAndRetainsGuard(){
        Fixture fixture=new Fixture();for(String candidate:Arrays.asList("awg","tcp",RESTRICTED))fixture.failures.put(candidate,Failure.BOOTSTRAP_UNAVAILABLE);
        fixture.connect();assertEquals(State.FAILED,fixture.core.state());assertTrue(fixture.guard);assertEquals(3,fixture.opens);
        assertTrue(fixture.time<=CONNECT_TIMEOUT_MS);assertEquals(0,fixture.active);
        fixture.core.lost(Failure.NETWORK);fixture.core.connect(Arrays.asList("awg"),null,null);assertEquals(3,fixture.opens);
    }
    @Test public void cancellationEveryPhaseReleasesExactlyOnce(){
        for(String target:Arrays.asList("awg","tcp","bootstrap","broker","dedicated")){
            Fixture fixture=new Fixture();
            if(!target.equals("awg"))fixture.failures.put("awg",Failure.NETWORK);
            if(!target.equals("awg")&&!target.equals("tcp"))fixture.failures.put("tcp",Failure.NETWORK);
            fixture.cancelCandidate=target.equals("awg")||target.equals("tcp")?target:RESTRICTED;
            fixture.cancelPhase=fixture.cancelCandidate.equals(RESTRICTED)?target:null;fixture.connect();
            assertEquals(target,State.DISCONNECTED,fixture.core.state());assertEquals(0,fixture.active);assertEquals(1,fixture.releases);
            fixture.core.disconnect();assertEquals(1,fixture.releases);assertFalse(fixture.guard);
        }
    }
    @Test public void authorizationConfigurationAndInternalAreTerminal(){
        for(Failure reason:Arrays.asList(Failure.AUTH,Failure.CONFIGURATION,Failure.INTERNAL)){
            Fixture fixture=new Fixture();fixture.failures.put("awg",reason);fixture.connect();
            assertEquals(State.FAILED,fixture.core.state());assertEquals(Arrays.asList("awg"),fixture.attempts);assertTrue(fixture.guard);
        }
    }
    @Test public void oneRestorationPassThenTerminalNoFlapping(){
        Fixture fixture=new Fixture();fixture.connect();fixture.failures.put("awg",Failure.NETWORK);fixture.core.lost(Failure.NETWORK);
        assertEquals("tcp",fixture.core.selected());assertEquals(1,fixture.count("restoration_succeeded"));assertTrue(fixture.guard);
        fixture.core.lost(Failure.NETWORK);int count=fixture.opens;
        for(int index=0;index<1000;index++)fixture.core.lost(Failure.NETWORK);
        assertEquals(State.FAILED,fixture.core.state());assertEquals(count,fixture.opens);assertEquals(0,fixture.active);assertEquals(1,fixture.peak);
    }
    @Test public void healthyPathHasNoProbeOrMigration(){
        Fixture fixture=new Fixture();fixture.failures.put("awg",Failure.NETWORK);fixture.connect();fixture.failures.clear();
        fixture.time+=24*3600000L;fixture.core.connect(Arrays.asList("awg","tcp"),"awg",null);
        assertEquals("tcp",fixture.core.selected());assertEquals(2,fixture.opens);
    }
    @Test public void restorationPrefersMostRecentlySuccessfulNormal(){
        Fixture fixture=new Fixture();fixture.failures.put("awg",Failure.NETWORK);fixture.connect();
        fixture.failures.remove("awg");fixture.failures.put("tcp",Failure.NETWORK);fixture.core.lost(Failure.NETWORK);
        assertEquals(Arrays.asList("awg","tcp","tcp","awg"),fixture.attempts);assertEquals("awg",fixture.core.selected());
    }
    @Test public void restoredAuthNeverCycles(){
        Fixture fixture=new Fixture();fixture.connect();fixture.core.lost(Failure.AUTH);
        assertEquals(State.FAILED,fixture.core.state());assertEquals(1,fixture.opens);assertTrue(fixture.guard);
        assertEquals(1,fixture.count("restoration_failed"));
    }
    @Test public void hintsAreFilteredAgainstCurrentConfig(){
        assertEquals(Arrays.asList("tcp","awg",RESTRICTED),order(Arrays.asList("awg","tcp","tcp"),"awg","tcp"));
        assertEquals(Arrays.asList("awg",RESTRICTED),order(Arrays.asList("awg"),"tcp",RESTRICTED));
        assertEquals(Arrays.asList(RESTRICTED),order(new ArrayList<>(),"https://room.invalid",null));
    }
    @Test public void restartNeverRestoresLiveState(){
        Fixture prior=new Fixture();prior.connect();Fixture restarted=new Fixture();restarted.hint=prior.hint;
        assertEquals(State.DISCONNECTED,restarted.core.state());assertNull(restarted.core.selected());assertEquals(0,restarted.opens);
        restarted.connect();assertEquals(Arrays.asList("awg"),restarted.attempts);
    }
    @Test public void cleanupFailureNeverOpensNextEngine(){
        Fixture fixture=new Fixture();fixture.cleanupFailure=true;fixture.connect();
        assertEquals(State.FAILED,fixture.core.state());assertEquals(0,fixture.opens);assertTrue(fixture.guard);
    }
    @Test public void failureClassificationIsExplicit(){
        assertEquals(Failure.AUTH,classify(new SecurityException()));assertEquals(Failure.CONFIGURATION,classify(new IllegalArgumentException()));
        assertEquals(Failure.NETWORK,classify(new java.io.IOException()));assertEquals(Failure.INTERNAL,classify(new UnsatisfiedLinkError()));
    }
    @Test public void candidateAndWholeConnectDeadlinesAreEnforced(){
        List<Long> budgets=new ArrayList<>();final long[] time={0};final int[] opens={0};
        Host host=new Host(){
            public long now(){return time[0];} public void pause(long millis){time[0]+=millis;}
            public void open(String candidate,long deadline){budgets.add(deadline-time[0]);opens[0]++;time[0]=deadline;}
            public void closeCandidate(){}public void release(){}public void remember(String candidate){fail();}public void event(Event event){}
        };
        ConnectivityOrchestrator core=new ConnectivityOrchestrator(host);core.connect(Arrays.asList("wg","awg","tcp"),null,null);
        assertEquals(State.FAILED,core.state());assertEquals(4,opens[0]);assertEquals(Long.valueOf(NORMAL_TIMEOUT_MS),budgets.get(0));
        assertTrue(budgets.get(3)<=RESTRICTED_TIMEOUT_MS);assertTrue(time[0]<=CONNECT_TIMEOUT_MS);
    }
    @Test public void crossThreadCancellationIsObservedWithoutWorkerQueue()throws Exception{
        CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
        Host host=new Host(){
            public long now(){return 0;}public void pause(long millis){}public void open(String candidate,long deadline)throws Exception{entered.countDown();assertTrue(release.await(2,TimeUnit.SECONDS));}
            public void closeCandidate(){}public void release(){}public void remember(String candidate){fail();}public void event(Event event){}
        };
        ConnectivityOrchestrator core=new ConnectivityOrchestrator(host);
        Thread worker=new Thread(()->core.connect(Arrays.asList("awg","tcp"),null,null));worker.start();
        assertTrue(entered.await(2,TimeUnit.SECONDS));core.interrupt(Failure.CANCELLED);release.countDown();worker.join(2000);
        assertFalse(worker.isAlive());assertEquals(State.DISCONNECTED,core.state());
    }
    @Test public void diagnosticsAreBoundedAndContainNoEndpoint(){
        Fixture fixture=new Fixture();
        for(int index=0;index<100;index++){fixture.connect();assertEquals(State.CONNECTED,fixture.core.state());fixture.core.disconnect();}
        assertEquals(MAX_EVENTS,fixture.core.events().size());
        for(Event event:fixture.core.events())if(event.candidate!=null)assertTrue(Arrays.asList("awg","tcp",RESTRICTED).contains(event.candidate));
    }
    @Test public void preStartCancellationNeverOpensCandidate(){
        Fixture fixture=new Fixture();fixture.core.interrupt(Failure.CANCELLED);fixture.connect();
        assertEquals(State.DISCONNECTED,fixture.core.state());assertEquals(0,fixture.opens);assertEquals(1,fixture.releases);
    }
}
