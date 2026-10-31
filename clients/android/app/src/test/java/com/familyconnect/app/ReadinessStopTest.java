package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessStopTest {
    @Test public void sharedDeadlineIsAvailabilityNotUserCancellation()throws Exception{
        assertEquals("NONE",ReadinessStop.reason(false,99,100));
        assertEquals("TIMEOUT",ReadinessStop.reason(false,100,100));
        ReadinessStop.check(false,99,100);
        try{ReadinessStop.check(false,100,100);fail();}
        catch(java.net.SocketTimeoutException expected){assertTrue(FriendsReadinessProtocol.unavailable(expected));}
    }
    @Test public void explicitCancellationWinsOverExpiredDeadline()throws Exception{
        assertEquals("CANCELLED",ReadinessStop.reason(true,101,100));
        try{ReadinessStop.check(true,101,100);fail();}
        catch(java.io.InterruptedIOException expected){assertFalse(FriendsReadinessProtocol.unavailable(expected));}
    }
    @Test public void validWarmCacheAndExistingGenerationRecoveryGuardStayIntact()throws Exception{
        byte[] cached=new byte[]{1,2,3};
        byte[] selected=RestrictedBootstrap.select(cached,true,false);
        assertArrayEquals(cached,selected);assertNotSame(cached,selected);
        try{RestrictedBootstrap.select(cached,true,true);fail();}
        catch(ConnectivityOrchestrator.Rejected expected){assertTrue(expected.temporaryBootstrap);}
        try{RestrictedBootstrap.select(null,true,true);fail();}
        catch(ConnectivityOrchestrator.Rejected expected){assertTrue(expected.temporaryBootstrap);}
        assertNull(RestrictedBootstrap.select(null,false,true));
    }
}
