package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class SubscriptionRefreshGateTest {
    @Test public void duplicateOpenRefreshIsSingleFlightUntilFinished(){
        var gate=new SubscriptionRefreshGate();var request=gate.begin();assertNotNull(request);assertNull(gate.begin());
        request.cancel();assertNull(gate.begin());gate.finish(request);assertNotNull(gate.begin());
    }
    @Test public void closedOwnerAndDismissedUiCannotCommit()throws Exception{
        var gate=new SubscriptionRefreshGate();var request=gate.begin();Object owner=new Object();
        assertTrue(request.bind(owner,"device"));gate.cancel();
        assertFalse(request.commit(owner,"device",()->fail("closed owner write")));
    }
    @Test public void oldIdentityAndOtherOwnerCannotCommit()throws Exception{
        var request=new SubscriptionRefreshGate().begin();Object owner=new Object();
        request.bind(owner,"original");
        assertFalse(request.commit(owner,"replacement",()->fail("other identity write")));
        assertFalse(request.commit(new Object(),"original",()->fail("other owner write")));
    }
    @Test public void successfulCommitRunsOnce()throws Exception{
        var request=new SubscriptionRefreshGate().begin();Object owner=new Object();int[] writes={0};request.bind(owner,"device");
        assertTrue(request.commit(owner,"device",()->writes[0]++));
        assertFalse(request.commit(owner,"device",()->writes[0]++));assertEquals(1,writes[0]);
    }
    @Test public void cancelledBeforeOwnerBindingIsNoOp(){
        var request=new SubscriptionRefreshGate().begin();request.cancel();assertFalse(request.bind(new Object(),"device"));
    }
    @Test public void failedCommitIsNotRetried()throws Exception{
        var request=new SubscriptionRefreshGate().begin();Object owner=new Object();request.bind(owner,"device");
        assertThrows(IllegalArgumentException.class,()->request.commit(owner,"device",()->{throw new IllegalArgumentException();}));
        assertFalse(request.commit(owner,"device",()->fail("retry")));
    }
}
