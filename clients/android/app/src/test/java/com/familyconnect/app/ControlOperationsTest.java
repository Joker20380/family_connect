package com.familyconnect.app;

import java.io.IOException;
import java.util.concurrent.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlOperationsTest {
    @Test public void liveLeaseBlocksImportsBetweenCallbacks() throws Exception {
        ControlOperations ops=new ControlOperations();Object owner=new Object();int[] writes={0};
        ops.claim(owner);ops.session(owner,()->writes[0]++);
        assertThrows(IOException.class,()->ops.edit(()->{},()->writes[0]++));
        assertThrows(IOException.class,()->ops.claim(new Object()));
        ops.session(owner,()->writes[0]++);assertEquals(2,writes[0]);
        ops.release(owner);ops.edit(()->{},()->writes[0]++);assertEquals(3,writes[0]);
    }
    @Test public void oldCleanupCannotReleaseNewSession() throws Exception {
        ControlOperations ops=new ControlOperations();Object old=new Object(),current=new Object();
        ops.claim(old);ops.release(old);ops.claim(current);
        assertThrows(ControlOperations.Stale.class,()->ops.release(old));
        assertThrows(ControlOperations.Stale.class,()->ops.session(old,()->fail("Stale callback ran")));
        assertThrows(IOException.class,()->ops.edit(()->{},()->fail("Edited active session")));
        ops.session(current,()->{});ops.release(current);
    }
    @Test public void failedCleanupKeepsLeaseUntilSuccessfulBarrier() throws Exception {
        ControlOperations ops=new ControlOperations();Object owner=new Object();ops.claim(owner);
        assertThrows(IllegalStateException.class,()->ops.session(owner,()->{throw new IllegalStateException("shutdown failed");}));
        assertThrows(IOException.class,()->ops.claim(new Object()));
        ops.session(owner,()->ops.release(owner));ops.claim(new Object());
    }
    @Test public void failedRecoveryNeverChangesProfile() throws Exception {
        ControlOperations ops=new ControlOperations();int[] writes={0};
        assertThrows(IOException.class,()->ops.edit(()->{throw new IOException("pending recovery");},()->writes[0]++));
        assertEquals(0,writes[0]);
        ops.edit(()->{},()->writes[0]++);assertEquals(1,writes[0]);
    }
    @Test public void recoveryThatStartsSessionCannotFallThroughToEdit() throws Exception {
        ControlOperations ops=new ControlOperations();Object restored=new Object();
        assertThrows(IOException.class,()->ops.edit(()->ops.claim(restored),()->fail("Restored session overwritten")));
        ops.release(restored);
    }
    @Test public void importAndServiceClaimAreSerialized() throws Exception {
        ControlOperations ops=new ControlOperations();ExecutorService pool=Executors.newFixedThreadPool(2);
        CountDownLatch editing=new CountDownLatch(1),finish=new CountDownLatch(1),claimStarted=new CountDownLatch(1);
        Object owner=new Object();
        try {
            Future<?> edit=pool.submit(()->{try{ops.edit(()->{},()->{editing.countDown();assertTrue(finish.await(3,TimeUnit.SECONDS));});}catch(Exception e){throw new RuntimeException(e);}});
            assertTrue(editing.await(3,TimeUnit.SECONDS));
            Future<?> claim=pool.submit(()->{claimStarted.countDown();try{ops.claim(owner);}catch(Exception e){throw new RuntimeException(e);}});
            assertTrue(claimStarted.await(3,TimeUnit.SECONDS));assertFalse(claim.isDone());
            finish.countDown();edit.get(3,TimeUnit.SECONDS);claim.get(3,TimeUnit.SECONDS);
            assertThrows(IOException.class,()->ops.edit(()->{},()->{}));ops.release(owner);
        } finally {finish.countDown();pool.shutdownNow();}
    }
    @Test public void controlReceiveAndRecoveryCannotBypassLegacySession() throws Exception {
        try(ControlTransactionTest.Harness h=new ControlTransactionTest.Harness()) {
            Object owner=new Object();ControlOperations.APP.claim(owner);
            try {
                assertThrows(IOException.class,()->h.receive("valid-wg"));
                assertThrows(IOException.class,h.core::recover);
                assertThrows(IOException.class,()->h.core.manual(()->fail("Manual bypass")));
                assertEquals(0,h.app.applies);
                assertTrue(h.core.flush(raw->true)); // Carrier still does not own VPN mutations.
            } finally {ControlOperations.APP.release(owner);}
            assertEquals("COMMITTED",h.receive("valid-wg"));
        }
    }
    @Test public void allPersistedAndInterruptedStateMarkersBlockLegacyMutation() throws Exception {
        java.nio.file.Path directory=java.nio.file.Files.createTempDirectory("control-presence-");
        try {
            for(String name:new String[]{"control-identity.enc","control-journal.enc"})
                for(String suffix:new String[]{"",".bak",".new"}) {
                    java.nio.file.Path marker=directory.resolve(name+suffix);java.nio.file.Files.write(marker,new byte[0]);
                    try {assertThrows(IOException.class,()->ControlStatePresence.requireUnmanaged(directory.toFile(),alias->false));}
                    finally {java.nio.file.Files.delete(marker);}
                }
            ControlStatePresence.requireUnmanaged(directory.toFile(),alias->false);
        } finally {java.nio.file.Files.delete(directory);}
    }
    @Test public void orphanKeysAndKeystoreErrorsCannotBypassGate() throws Exception {
        java.nio.file.Path directory=java.nio.file.Files.createTempDirectory("control-orphan-");
        try {
            for(String name:new String[]{"family-connect-control-identity-v1","family-connect-control-journal-v1"})
                assertThrows(IOException.class,()->ControlStatePresence.requireUnmanaged(directory.toFile(),name::equals));
            assertThrows(IOException.class,()->ControlStatePresence.requireUnmanaged(directory.toFile(),alias->{throw new IOException("locked");}));
        } finally {java.nio.file.Files.delete(directory);}
    }
    @Test public void nullTokenCannotAcquireOrRelease() throws Exception {
        ControlOperations ops=new ControlOperations();
        assertThrows(NullPointerException.class,()->ops.claim(null));
        assertThrows(ControlOperations.Stale.class,()->ops.release(null));
        assertThrows(ControlOperations.Stale.class,()->ops.session(null,()->fail("Null owner")));
    }
}
