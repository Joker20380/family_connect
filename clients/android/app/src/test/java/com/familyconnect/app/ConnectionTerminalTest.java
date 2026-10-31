package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ConnectionTerminalTest {
    @Test public void failedSeriesIsWaitingNotTerminalSuccess(){
        ConnectionTerminal model=new ConnectionTerminal();long old=model.begin(ConnectionTerminal.Stage.RESTORING);
        model.event(old,new ConnectivityOrchestrator.Event("restoration_failed",null,ConnectivityOrchestrator.Failure.NETWORK,ConnectivityOrchestrator.State.RESTORING,1));
        model.event(old,new ConnectivityOrchestrator.Event("recovery_wait",null,ConnectivityOrchestrator.Failure.NETWORK,ConnectivityOrchestrator.State.RESTORING,2));
        assertFalse(model.snapshot().finished);assertFalse(model.snapshot().success);assertTrue(model.snapshot().lines.contains(ConnectionTerminal.Stage.RETRY_WAIT));
        long current=model.begin(ConnectionTerminal.Stage.RESTORING);model.event(old,new ConnectivityOrchestrator.Event("candidate_succeeded","restricted",null,ConnectivityOrchestrator.State.CONNECTED,3));
        assertFalse(model.snapshot().success);model.end(current,ConnectionTerminal.Stage.CANCELLED,false);assertFalse(model.snapshot().success);
    }
    @Test public void homeUsesOnlyCurrentVpnState(){
        ConnectionTerminal vpn=new ConnectionTerminal();
        assertEquals(0,ConnectionTerminal.homePane("off",vpn.snapshot()));
        long old=vpn.begin(ConnectionTerminal.Stage.PREPARING);
        for(String state:new String[]{"connecting","reconnecting","restoring"})assertEquals(1,ConnectionTerminal.homePane(state,vpn.snapshot()));
        vpn.end(old,ConnectionTerminal.Stage.FAILED,false);assertEquals(1,ConnectionTerminal.homePane("off",vpn.snapshot()));
        long current=vpn.begin(ConnectionTerminal.Stage.PREPARING);vpn.end(current,ConnectionTerminal.Stage.VPN_READY,true);
        vpn.end(old,ConnectionTerminal.Stage.FAILED,false);assertEquals(0,ConnectionTerminal.homePane("on",vpn.snapshot()));
        vpn.end(vpn.begin(ConnectionTerminal.Stage.PREPARING),ConnectionTerminal.Stage.CANCELLED,false);
        assertEquals(0,ConnectionTerminal.homePane("off",vpn.snapshot()));
    }
    @Test public void cancelledReturnsInactivePane(){
        ConnectionTerminal vpn=new ConnectionTerminal(),chat=new ConnectionTerminal();
        long attempt=vpn.begin(ConnectionTerminal.Stage.TELEMOST);
        vpn.end(attempt,ConnectionTerminal.Stage.CANCELLED,false);
        assertEquals(0,ConnectionTerminal.pane("off",vpn.snapshot(),chat.snapshot()));
    }
    @Test public void terminalReplacesTelemetryUntilReady(){
        ConnectionTerminal vpn=new ConnectionTerminal(),chat=new ConnectionTerminal();
        assertEquals(0,ConnectionTerminal.pane("off",vpn.snapshot(),chat.snapshot()));
        long attempt=vpn.begin(ConnectionTerminal.Stage.PREPARING);
        for(String state:new String[]{"connecting","reconnecting","restoring"})assertEquals(1,ConnectionTerminal.pane(state,vpn.snapshot(),chat.snapshot()));
        vpn.end(attempt,ConnectionTerminal.Stage.VPN_READY,true);
        assertEquals(0,ConnectionTerminal.pane("on",vpn.snapshot(),chat.snapshot()));
        attempt=vpn.begin(ConnectionTerminal.Stage.RESTORING);vpn.end(attempt,ConnectionTerminal.Stage.FAILED,false);
        assertEquals(1,ConnectionTerminal.pane("off",vpn.snapshot(),chat.snapshot()));
        chat.begin(ConnectionTerminal.Stage.CHAT_ENROLL);
        assertEquals(2,ConnectionTerminal.pane("off",vpn.snapshot(),chat.snapshot()));
        assertEquals(0,ConnectionTerminal.pane("on",vpn.snapshot(),chat.snapshot()));
    }
    @Test public void staleAndTerminalEventsCannotRewriteAttempt(){
        ConnectionTerminal model=new ConnectionTerminal();long old=model.begin(ConnectionTerminal.Stage.PREPARING);long current=model.begin(ConnectionTerminal.Stage.PREPARING);
        model.end(old,ConnectionTerminal.Stage.VPN_READY,true);assertFalse(model.snapshot().finished);
        model.end(current,ConnectionTerminal.Stage.CANCELLED,false);model.end(current,ConnectionTerminal.Stage.VPN_READY,true);
        assertEquals(ConnectionTerminal.Stage.CANCELLED,model.snapshot().lines.get(1));assertFalse(model.snapshot().success);
    }
    @Test public void failureSurvivesCleanup(){
        ConnectionTerminal model=new ConnectionTerminal();long attempt=model.begin(ConnectionTerminal.Stage.TELEMOST);
        model.end(attempt,ConnectionTerminal.Stage.AUTH,false);model.end(attempt,ConnectionTerminal.Stage.CANCELLED,false);
        assertEquals(ConnectionTerminal.Stage.AUTH,model.snapshot().lines.get(1));
    }
    @Test public void boundedAndImmutable(){
        ConnectionTerminal model=new ConnectionTerminal();long attempt=model.begin(ConnectionTerminal.Stage.PREPARING);
        for(int count=0;count<100;count++){model.add(attempt,ConnectionTerminal.Stage.TCP);model.add(attempt,ConnectionTerminal.Stage.UNAVAILABLE);}
        assertEquals(12,model.snapshot().lines.size());assertThrows(UnsupportedOperationException.class,()->model.snapshot().lines.clear());
    }
    @Test public void actualSuccessOnly(){
        ConnectionTerminal model=new ConnectionTerminal();long attempt=model.begin(ConnectionTerminal.Stage.PREPARING);
        model.event(attempt,new ConnectivityOrchestrator.Event("candidate_attempted","tcp",null,ConnectivityOrchestrator.State.CONNECTING,0));assertFalse(model.snapshot().success);assertFalse(model.snapshot().lines.contains(ConnectionTerminal.Stage.TELEMOST));
        model.event(attempt,new ConnectivityOrchestrator.Event("candidate_succeeded","tcp",null,ConnectivityOrchestrator.State.CONNECTED,1));assertTrue(model.snapshot().success);
    }
}
