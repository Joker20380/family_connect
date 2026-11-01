package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public final class Ui60PresentationTest {
    @Test public void failedRouteCanBeSelectedWithoutUnlockingTransitions(){
        for(String state:new String[]{"off","on","failed"})assertTrue(state,Ui60Presentation.canSelectRoute(state,false));
        for(String state:new String[]{"connecting","restoring","disconnecting","cleanup-required","tun-created",null})assertFalse(state,Ui60Presentation.canSelectRoute(state,false));
        for(String state:new String[]{"off","on","failed"})assertFalse(state,Ui60Presentation.canSelectRoute(state,true));
    }
    @Test public void failedAndCleanupActionsAreDisconnectNotConnect(){
        assertEquals(R.string.connect,Ui60Presentation.action("off"));
        for(String state:new String[]{"on","failed","cleanup-required"})assertEquals(state,R.string.disconnect,Ui60Presentation.action(state));
        for(String state:new String[]{"connecting","restoring","disconnecting","tun-created",null})assertEquals(state,android.R.string.cancel,Ui60Presentation.action(state));
    }
    @Test public void terminalFailureIsNotPresentedAsPending(){
        for(String state:new String[]{"off","on","failed","cleanup-required"})assertFalse(state,Ui60Presentation.pending(state));
        for(String state:new String[]{"connecting","restoring","disconnecting","tun-created"})assertTrue(state,Ui60Presentation.pending(state));
    }
    @Test public void queuedRouteWaitsForCompletedCleanupAndIdleUi(){
        for(String state:new String[]{"on","failed","connecting","restoring","disconnecting","cleanup-required",null})assertFalse(state,Ui60Presentation.canReconnect(state,false,true));
        assertFalse(Ui60Presentation.canReconnect("off",true,true));
        assertFalse(Ui60Presentation.canReconnect("off",false,false));
        assertTrue(Ui60Presentation.canReconnect("off",false,true));
    }
    @Test public void batteryBarUsesOnlyValidObservedPercent(){
        assertEquals(0f,Ui60Presentation.batteryFraction("0%"),0f);
        assertEquals(.42f,Ui60Presentation.batteryFraction("42%"),0f);
        assertEquals(1f,Ui60Presentation.batteryFraction("100%"),0f);
        for(String value:new String[]{null,"—","42","101%","-1%","unknown%"})assertEquals(-1f,Ui60Presentation.batteryFraction(value),0f);
    }
    @Test public void truthfulStates(){
        assertEquals(R.string.off,Ui60Presentation.status("off",false));
        assertEquals(R.string.connecting,Ui60Presentation.status("connecting",false));
        assertEquals(R.string.on,Ui60Presentation.status("on",false));
        assertEquals(R.string.ui_disconnecting,Ui60Presentation.status("disconnecting",false));
        assertEquals(R.string.ui_cleanup_required,Ui60Presentation.status("cleanup-required",false));
        assertEquals(R.string.restoring,Ui60Presentation.status("restoring",false));
        assertEquals(R.string.unable_connect,Ui60Presentation.status("failed",true));
        assertEquals(R.string.unable_connect,Ui60Presentation.status("off",true));
        assertEquals(R.string.connecting,Ui60Presentation.status("tun-created",false));
    }
    @Test public void previewDoesNotStealMinimumControlsSpace(){
        assertEquals(209,Ui60Presentation.dialHeight(348,780,120));
        assertEquals(166,Ui60Presentation.dialHeight(276,640,120));
        assertEquals(120,Ui60Presentation.dialHeight(736,392,120));
        assertEquals(188,Ui60Presentation.compactDialHeight(209,120,21));
        assertEquals(120,Ui60Presentation.compactDialHeight(166,120,300));
        assertEquals(209,Ui60Presentation.compactDialHeight(209,120,-30));
        assertEquals(156,Ui60Presentation.mapHeight(368,6,145f/360f));
        assertEquals(127,Ui60Presentation.mapHeight(296,6,145f/360f));
        assertEquals(311,Ui60Presentation.mapHeight(736,12,145f/360f));
        assertEquals(161,Ui60Presentation.mapHeight(368,6,150f/360f));
    }
}
