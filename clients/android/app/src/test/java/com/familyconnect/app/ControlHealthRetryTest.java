package com.familyconnect.app;

import org.junit.Test;
import java.util.concurrent.atomic.*;
import static org.junit.Assert.*;

public class ControlHealthRetryTest {
    @Test public void waitsForNetworkAndTransientProbeFailure()throws Exception {
        AtomicLong now=new AtomicLong();AtomicInteger calls=new AtomicInteger();
        assertTrue(ControlHealthRetry.check(()->calls.incrementAndGet()==3,()->false,
            now::get,now::addAndGet,15000));
        assertEquals(200,now.get());assertEquals(3,calls.get());
    }
    @Test public void unavailableNetworkStopsAtDeadline()throws Exception {
        AtomicLong now=new AtomicLong();AtomicInteger calls=new AtomicInteger();
        assertFalse(ControlHealthRetry.check(()->{calls.incrementAndGet();return false;},()->false,
            now::get,now::addAndGet,250));
        assertEquals(250,now.get());assertEquals(3,calls.get());
    }
    @Test public void lateSuccessCannotCommit()throws Exception {
        AtomicLong now=new AtomicLong();
        assertFalse(ControlHealthRetry.check(()->{now.set(15000);return true;},()->false,
            now::get,ms->{fail("No retry after expired deadline");},15000));
    }
    @Test public void cancellationDuringProbeRejectsSuccess()throws Exception {
        AtomicBoolean cancelled=new AtomicBoolean();
        assertFalse(ControlHealthRetry.check(()->{cancelled.set(true);return true;},cancelled::get,
            ()->0,ms->{fail("No retry after cancel");},15000));
    }
    @Test public void cancellationDuringWaitDoesNotProbeAgain()throws Exception {
        AtomicBoolean cancelled=new AtomicBoolean();AtomicInteger calls=new AtomicInteger();
        assertFalse(ControlHealthRetry.check(()->{calls.incrementAndGet();return false;},cancelled::get,
            ()->0,ms->cancelled.set(true),15000));assertEquals(1,calls.get());
    }
    @Test(expected=InterruptedException.class) public void interruptedWaitStops()throws Exception {
        ControlHealthRetry.check(()->false,()->false,()->0,ms->{throw new InterruptedException();},15000);
    }
}
