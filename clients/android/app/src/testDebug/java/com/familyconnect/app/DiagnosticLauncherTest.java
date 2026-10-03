package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public final class DiagnosticLauncherTest {
    private static final class Platform implements DiagnosticLauncher.Host<String> {
        String launcher="com.familyconnect.app.FriendsActivity",started;
        boolean resolutionFails,startFails;
        public String resolve(){if(resolutionFails)throw new IllegalStateException();return launcher;}
        public void start(String component){if(startFails)throw new IllegalStateException();started=component;}
    }
    @Test public void friendsWithoutMainActivityUsesResolvedLauncher(){
        Platform platform=new Platform();assertTrue(DiagnosticLauncher.open(platform));
        assertEquals("com.familyconnect.app.FriendsActivity",platform.started);
    }
    @Test public void alternateLauncherIsNotHardcoded(){
        Platform platform=new Platform();platform.launcher="another.variant.Launcher";
        assertTrue(DiagnosticLauncher.open(platform));assertEquals(platform.launcher,platform.started);
    }
    @Test public void missingLauncherFailsWithoutStarting(){
        Platform platform=new Platform();platform.launcher=null;
        assertFalse(DiagnosticLauncher.open(platform));assertNull(platform.started);
    }
    @Test public void resolutionExceptionIsBounded(){
        Platform platform=new Platform();platform.resolutionFails=true;
        assertFalse(DiagnosticLauncher.open(platform));assertNull(platform.started);
    }
    @Test public void missingActivityAtLaunchIsBounded(){
        Platform platform=new Platform();platform.startFails=true;
        assertFalse(DiagnosticLauncher.open(platform));assertNull(platform.started);
    }
}
