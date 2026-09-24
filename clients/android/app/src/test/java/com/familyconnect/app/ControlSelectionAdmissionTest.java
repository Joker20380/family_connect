package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ControlSelectionAdmissionTest {
    private String select(ControlSelectionTest.Harness h)throws Exception {
        return ControlSelection.select(h.core,h.identity,ControlIntakeTest.enrollment(h.identity),"second-node",()->h.host.active!=null);
    }
    @Test public void connectedSwitchAndDisconnectedRetryUseSameJournal()throws Exception {
        try(var h=new ControlSelectionTest.Harness()) {
            assertEquals("SELECTED",select(h));int writes=h.host.saves,starts=h.host.starts;
            assertEquals("SELECTED",select(h));assertEquals(starts,h.host.starts);assertEquals(writes,h.host.saves);
            h.host.stop();assertEquals("SELECTED",select(h));assertEquals(starts+1,h.host.starts);assertEquals(writes,h.host.saves);
        }
    }
    @Test public void enrollmentFailureCannotMutateVpnOrJournal()throws Exception {
        for(int mode=0;mode<3;mode++)try(var h=new ControlSelectionTest.Harness()) {
            var e=ControlIntakeTest.enrollment(h.identity);
            if(mode==0)e.addProperty("phase","READY");if(mode==1)e.addProperty("device","0".repeat(32));if(mode==2)e.addProperty("origin","http://enroll.example");
            byte[] prior=h.store.raw.clone();int writes=h.host.saves;
            assertThrows(Exception.class,()->ControlSelection.select(h.core,h.identity,e,"second-node",()->true));
            assertArrayEquals(prior,h.store.raw);assertEquals(writes,h.host.saves);
        }
    }
    @Test public void failedRecoveryCannotStartNewSelection()throws Exception {
        try(var h=new ControlSelectionTest.Harness()) {
            h.host.failStop=true;assertEquals("FAILED",select(h));int writes=h.host.saves;
            assertEquals("FAILED",select(h));assertEquals(writes,h.host.saves);
            h.host.failStop=false;assertEquals("SELECTED",select(h));
        }
    }
    @Test public void repeatedSelectionDoesNotClaimSuccessWhenReconnectHealthFails()throws Exception {
        try(var h=new ControlSelectionTest.Harness()) {
            assertEquals("SELECTED",select(h));h.host.stop();h.host.good=false;
            assertThrows(Exception.class,()->select(h));assertNull(h.host.active);
        }
    }
}
