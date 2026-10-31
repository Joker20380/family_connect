package com.familyconnect.app;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;

final class ConnectivityOrchestrator {
    enum State { DISCONNECTED, CONNECTING, CONNECTED, RESTORING, FAILED, DISCONNECTING }
    enum Failure { CANCELLED, AUTH, CONFIGURATION, NETWORK, TRANSPORT_UNAVAILABLE, BOOTSTRAP_UNAVAILABLE, INTERNAL }
    static final long NORMAL_TIMEOUT_MS=20000, RESTRICTED_TIMEOUT_MS=200000, CONNECT_TIMEOUT_MS=300000;
    static final int MAX_EVENTS=128, MAX_RESTORATIONS=1;
    static final int MAX_BOOTSTRAP_RECOVERIES=2;
    static final long RECOVERY_BACKOFF_MS=30000, MAX_RECOVERY_BACKOFF_MS=120000;
    static final long RECOVERY_COOLDOWN_MS=300000, STABLE_TRAFFIC_MS=120000;
    static final String RESTRICTED="restricted";
    static final class Rejected extends Exception {
        final Failure category;
        final boolean temporaryBootstrap;
        Rejected(Failure category) { this(category,false); }
        Rejected(Failure category,boolean temporaryBootstrap) {
            super(category.name());this.category=category;
            this.temporaryBootstrap=category==Failure.BOOTSTRAP_UNAVAILABLE&&temporaryBootstrap;
        }
    }
    static final class Event {
        final String name,candidate;
        final Failure failure;
        final State state;
        final long elapsedMs;
        Event(String name,String candidate,Failure failure,State state,long elapsedMs) {
            this.name=name;this.candidate=candidate;this.failure=failure;this.state=state;this.elapsedMs=elapsedMs;
        }
    }
    interface Host {
        long now();
        default long jitter(long maximum) { return 0; }
        default boolean networkAvailable() { return true; }
        default List<String> configure(List<String> configured,long deadline) throws Exception { return configured; }
        void pause(long millis) throws Exception;
        void open(String candidate,long deadline) throws Exception;
        void closeCandidate() throws Exception;
        void release() throws Exception;
        void remember(String candidate);
        void event(Event event);
    }
    private final Host host;
    private final ArrayDeque<Event> events=new ArrayDeque<>();
    private List<String> candidates=Collections.emptyList();
    private volatile Failure interrupted;
    private volatile State state=State.DISCONNECTED;
    private String selected;
    private long started;
    private int restorations;
    private volatile boolean requested;
    private long retryAt;
    private int failedSeries;
    private Failure retryReason;
    private int bootstrapRecoveries;
    private long healthySince=-1;
    ConnectivityOrchestrator(Host host) { this.host=host; }
    State state() { return state; }
    String selected() { return selected; }
    synchronized List<Event> events() { return new ArrayList<>(events); }
    static List<String> order(List<String> configured,String preferred,String lastGood) {
        LinkedHashSet<String> allowed=new LinkedHashSet<>();
        for(String candidate:configured) { Transport.parse(candidate);allowed.add(candidate); }
        List<String> ordered=new ArrayList<>();
        if(allowed.remove(lastGood))ordered.add(lastGood);
        if(allowed.remove(preferred))ordered.add(preferred);
        ordered.addAll(allowed);ordered.add(RESTRICTED);
        return Collections.unmodifiableList(ordered);
    }
    void connect(List<String> configured,String preferred,String lastGood) {
        if(state!=State.DISCONNECTED)return;
        started=host.now();restorations=0;failedSeries=0;bootstrapRecoveries=0;retryAt=0;requested=true;state=State.CONNECTING;emit("connect_requested",null,null);
        try { candidates=order(host.configure(configured,started+30000),preferred,lastGood);check(started+CONNECT_TIMEOUT_MS); }
        catch(Exception|LinkageError failure) { finish(interrupted!=null?interrupted:classify(failure),false);return; }
        run(false);
    }
    void interrupt(Failure reason) {
        if(reason!=Failure.CANCELLED&&reason!=Failure.AUTH)throw new IllegalArgumentException();
        interrupted=reason;
        requested=false;
    }
    void check(long deadline) throws Rejected {
        if(interrupted!=null)throw new Rejected(interrupted);
        if(host.now()>=deadline)throw new Rejected(Failure.NETWORK);
    }
    void lost(Failure reason) {
        if(state!=State.CONNECTED)return;
        if(interrupted!=null)reason=interrupted;
        emit("transport_lost",selected,reason);
        state=State.RESTORING;started=host.now();
        if(!retryable(reason)||restorations++>=MAX_RESTORATIONS) { finish(reason,true);return; }
        emit("restoration_attempted",selected,reason);
        List<String> normal=new ArrayList<>(candidates);normal.remove(RESTRICTED);
        candidates=order(normal,selected,selected);
        run(true);
    }
    void retryIfDue() {
        if(state!=State.RESTORING)return;
        if(interrupted!=null){finish(interrupted,true);return;}
        if(!requested||retryAt==0||host.now()<retryAt)return;
        retryAt=0;restorations=1;started=host.now();
        emit("restoration_attempted",selected,retryReason);
        run(true);
    }
    boolean needsPolling(){return state==State.CONNECTED||state==State.RESTORING;}
    void trafficHealthy(boolean good) {
        if(state!=State.CONNECTED||!good){healthySince=-1;return;}
        if(healthySince<0)healthySince=host.now();
        if(host.now()-healthySince>=STABLE_TRAFFIC_MS){restorations=0;failedSeries=0;bootstrapRecoveries=0;}
    }
    private void run(boolean restoring) {
        long deadline=started+CONNECT_TIMEOUT_MS;
        Failure last=Failure.TRANSPORT_UNAVAILABLE;
        boolean temporaryBootstrap=false;
        for(int index=0;index<candidates.size();index++) {
            String candidate=candidates.get(index);
            try {
                check(deadline);host.closeCandidate();check(deadline);
                if(!host.networkAvailable())throw new Rejected(Failure.TRANSPORT_UNAVAILABLE);
                if(index>0||restoring) {
                    emit("fallback",candidate,last);
                    long until=Math.min(deadline,host.now()+Math.min(4000,1000L<<index));
                    while(host.now()<until) { check(deadline);host.pause(Math.min(100,until-host.now())); }
                }
                check(deadline);emit("candidate_attempted",candidate,null);
                long candidateDeadline=Math.min(deadline,host.now()+(RESTRICTED.equals(candidate)?RESTRICTED_TIMEOUT_MS:NORMAL_TIMEOUT_MS));
                host.open(candidate,candidateDeadline);check(candidateDeadline);
                selected=candidate;state=State.CONNECTED;retryAt=0;healthySince=-1;
                if(!RESTRICTED.equals(candidate))host.remember(candidate);
                emit("candidate_succeeded",candidate,null);emit("time_to_connected",candidate,null);
                if(restoring)emit("restoration_succeeded",candidate,null);
                return;
            } catch(Exception|LinkageError failure) {
                last=interrupted!=null?interrupted:classify(failure);
                temporaryBootstrap=interrupted==null&&failure instanceof Rejected&&((Rejected)failure).temporaryBootstrap;
                emit("candidate_failed",candidate,last);
                try { host.closeCandidate(); }
                catch(Exception|LinkageError cleanup) { finish(Failure.INTERNAL,restoring);return; }
                if(terminal(last)||host.now()>=deadline) { finish(last,restoring,temporaryBootstrap);return; }
            }
        }
        finish(last,restoring,temporaryBootstrap);
    }
    static Failure classify(Throwable failure) {
        if(failure instanceof Rejected)return ((Rejected)failure).category;
        if(failure instanceof SecurityException)return Failure.AUTH;
        if(failure instanceof IllegalArgumentException)return Failure.CONFIGURATION;
        if(failure instanceof java.io.IOException)return Failure.NETWORK;
        return Failure.INTERNAL;
    }
    private static boolean terminal(Failure reason) {
        return reason==Failure.CANCELLED||reason==Failure.AUTH||reason==Failure.CONFIGURATION||reason==Failure.INTERNAL;
    }
    private static boolean retryable(Failure reason){return reason==Failure.NETWORK||reason==Failure.TRANSPORT_UNAVAILABLE;}
    private void finish(Failure reason,boolean restoring) {
        finish(reason,restoring,false);
    }
    private void finish(Failure reason,boolean restoring,boolean temporaryBootstrap) {
        try { host.closeCandidate(); } catch(Exception|LinkageError failure) { reason=Failure.INTERNAL; }
        selected=null;
        if(reason==Failure.CANCELLED) { disconnect();return; }
        boolean bootstrapRetry=reason==Failure.BOOTSTRAP_UNAVAILABLE&&temporaryBootstrap;
        if(requested&&(retryable(reason)||bootstrapRetry)&&!candidates.isEmpty()){
            if(bootstrapRetry)bootstrapRecoveries++;
            long delay=Math.min(MAX_RECOVERY_BACKOFF_MS,RECOVERY_BACKOFF_MS<<Math.min(failedSeries,2));
            if(bootstrapRetry&&bootstrapRecoveries>MAX_BOOTSTRAP_RECOVERIES){delay=RECOVERY_COOLDOWN_MS;bootstrapRecoveries=0;}
            delay+=Math.max(0,Math.min(5000,host.jitter(5000)));
            failedSeries=Math.min(2,failedSeries+1);retryReason=reason;retryAt=host.now()+delay;
            state=State.RESTORING;emit("restoration_failed",null,reason);emit("recovery_wait",null,reason);return;
        }
        requested=false;retryAt=0;
        state=State.FAILED;
        emit(restoring?"restoration_failed":"connect_failed",null,reason);
    }
    void disconnect() {
        requested=false;retryAt=0;
        if(state==State.DISCONNECTED)return;
        interrupted=Failure.CANCELLED;state=State.DISCONNECTING;emit("disconnect_requested",selected,Failure.CANCELLED);
        try { host.closeCandidate();host.release();selected=null;state=State.DISCONNECTED;emit("disconnected",null,Failure.CANCELLED);interrupted=null; }
        catch(Exception|LinkageError failure) { state=State.FAILED;emit("cleanup_failed",selected,Failure.INTERNAL); }
    }
    private synchronized void emit(String name,String candidate,Failure failure) {
        Event event=new Event(name,candidate,failure,state,Math.max(0,host.now()-started));
        if(events.size()==MAX_EVENTS)events.removeFirst();events.addLast(event);host.event(event);
    }
}
