package com.familyconnect.app;

import java.io.IOException;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlStartupTest {
    private static void run(boolean connect,ControlStartup.Presence presence,ControlStartup.Recovery recovery,
                            ControlStartup.Connect legacy)throws Exception {
        ControlStartup.run(connect,presence,recovery,()->{},legacy);
    }
    @Test public void onlyExplicitIdleStartupResumes()throws Exception {
        for(boolean connect:new boolean[]{false,true})for(String outcome:new String[]{"IDLE","ROLLED_BACK"}) {
            int[] resumes={0};
            ControlStartup.run(connect,()->true,()->outcome,()->resumes[0]++,()->fail("Legacy bypass"));
            assertEquals(connect&&outcome.equals("IDLE")?1:0,resumes[0]);
        }
    }
    @Test public void resumeFailureCannotFallThroughToLegacy() {
        assertThrows(IOException.class,()->ControlStartup.run(true,()->true,()->"IDLE",
            ()->{throw new IOException("Expired");},()->fail("Legacy bypass")));
    }

    @Test public void explicitUnmanagedConnectOnly() throws Exception {
        int[] connects={0};
        run(false,()->false,()->{throw new AssertionError();},()->connects[0]++);
        assertEquals(0,connects[0]);
        run(true,()->false,()->{throw new AssertionError();},()->connects[0]++);
        assertEquals(1,connects[0]);
    }
    @Test public void managedNeverFallsThroughEvenWhenIdle() throws Exception {
        for(boolean connect:new boolean[]{false,true})for(String outcome:new String[]{"IDLE","ROLLED_BACK"}){
            int[] recoveries={0};
            run(connect,()->true,()->{recoveries[0]++;return outcome;},()->fail("Legacy bypass"));
            assertEquals(1,recoveries[0]);
        }
    }
    @Test public void unavailableKeystoreFailsClosed() {
        assertThrows(IOException.class,()->run(true,()->{throw new IOException("locked");},
            ()->{throw new AssertionError("Recovery with unknown state");},()->fail("Legacy bypass")));
    }
    @Test public void failedOrUnexpectedRecoveryFailsClosed() {
        for(String outcome:new String[]{"FAILED","COMMITTED",null})
            assertThrows(IOException.class,()->run(true,()->true,()->outcome,()->fail("Legacy bypass")));
        assertThrows(IOException.class,()->run(true,()->true,()->{throw new IOException("orphan identity");},()->fail("Legacy bypass")));
    }
    @Test public void processRestartRollsBackBeforeAnyLegacyConnect() throws Exception {
        try(ControlTransactionTest.Harness h=new ControlTransactionTest.Harness()) {
            h.app.crashApply=true;
            assertThrows(ControlTransactionTest.Death.class,()->h.receive("valid-wg"));
            h.restart();
            run(true,()->true,h.core::recover,()->fail("Legacy bypass"));
            assertEquals(1,h.app.rollbacks);assertEquals("IDLE",h.state().get("phase").getAsString());
            assertEquals(1,h.state().get("floor").getAsLong());
            run(true,()->true,h.core::recover,()->fail("Legacy bypass"));
            assertEquals(1,h.app.rollbacks);
            assertEquals("ROLLED_BACK",h.receive("valid-wg"));assertEquals(1,h.app.applies);
        }
    }
    @Test public void failedShutdownPreservesPendingForLaterStartup() throws Exception {
        try(ControlTransactionTest.Harness h=new ControlTransactionTest.Harness()) {
            h.app.crashApply=true;assertThrows(ControlTransactionTest.Death.class,()->h.receive("valid-wg"));
            h.restart();h.app.failRollback=true;
            assertThrows(IOException.class,()->run(true,()->true,h.core::recover,()->fail("Legacy bypass")));
            assertEquals("ROLLING_BACK",h.state().get("phase").getAsString());
            assertFalse(h.state().get("staged").isJsonNull());
            h.restart();h.app.failRollback=false;
            run(false,()->true,h.core::recover,()->fail("Legacy bypass"));
            assertEquals("IDLE",h.state().get("phase").getAsString());assertEquals(1,h.state().get("floor").getAsLong());
        }
    }
    @Test public void committedStartupDoesNotReapplyOrLoseReceipts() throws Exception {
        try(ControlTransactionTest.Harness h=new ControlTransactionTest.Harness()) {
            assertEquals("COMMITTED",h.receive("valid-wg"));int receipts=h.state().getAsJsonArray("outbox").size();
            h.restart();
            run(true,()->true,h.core::recover,()->fail("Legacy bypass"));
            assertEquals(1,h.app.applies);assertEquals(0,h.app.rollbacks);
            assertEquals(receipts,h.state().getAsJsonArray("outbox").size());assertEquals(1,h.state().get("floor").getAsLong());
        }
    }
}
