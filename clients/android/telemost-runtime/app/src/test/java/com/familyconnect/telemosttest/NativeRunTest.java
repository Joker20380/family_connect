package com.familyconnect.telemosttest;

import org.junit.Test;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;

public class NativeRunTest {
    @Test public void closedPipeDuringCancellationStillAllowsGracefulExit() throws Exception {
        NativeRun run = new NativeRun();
        CountDownLatch reading = new CountDownLatch(1);
        CountDownLatch pipeClosed = new CountDownLatch(1);
        CountDownLatch exited = new CountDownLatch(1);
        AtomicBoolean destroying = new AtomicBoolean();
        AtomicBoolean forced = new AtomicBoolean();
        Process child = new Process() {
            public java.io.OutputStream getOutputStream() { return new java.io.ByteArrayOutputStream(); }
            public java.io.InputStream getErrorStream() { return new java.io.ByteArrayInputStream(new byte[0]); }
            public java.io.InputStream getInputStream() {
                return new java.io.InputStream() {
                    public int read() throws java.io.IOException {
                        reading.countDown();
                        try { pipeClosed.await(); } catch (InterruptedException error) { throw new java.io.IOException(error); }
                        throw new java.io.IOException("closed by Process.destroy");
                    }
                };
            }
            public int waitFor() throws InterruptedException { exited.await(); return 143; }
            public boolean waitFor(long timeout, TimeUnit unit) throws InterruptedException { return exited.await(timeout, unit); }
            public int exitValue() { if (isAlive()) throw new IllegalThreadStateException(); return 143; }
            public boolean isAlive() { return exited.getCount() != 0; }
            public void destroy() {
                if (!destroying.compareAndSet(false, true)) return;
                pipeClosed.countDown();
                new Thread(() -> {
                    try { Thread.sleep(150); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
                    exited.countDown();
                }).start();
            }
            public Process destroyForcibly() { forced.set(true); exited.countDown(); return this; }
        };
        AtomicInteger code = new AtomicInteger();
        run.start(() -> child, new NativeRun.Observer() {
            public void line(String line) {}
            public void finished(int exit, boolean cancelled) { code.set(exit); }
        });
        assertTrue(reading.await(3, TimeUnit.SECONDS));
        run.cancel();
        run.awaitForTest(3000);
        assertFalse(run.isActive());
        assertFalse(forced.get());
        assertEquals(143, code.get());
    }

    @Test public void cancellationDuringSpawnIsNotLost() throws Exception {
        NativeRun run = new NativeRun();
        CountDownLatch spawning = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        AtomicBoolean cancelled = new AtomicBoolean();
        run.start(() -> {
            spawning.countDown();
            assertTrue(release.await(3, TimeUnit.SECONDS));
            return new ProcessBuilder("sh", "-c", "exec sleep 30").start();
        }, new NativeRun.Observer() {
            public void line(String line) {}
            public void finished(int code, boolean wasCancelled) { cancelled.set(wasCancelled); }
        });
        assertTrue(spawning.await(3, TimeUnit.SECONDS));
        run.cancel();
        release.countDown();
        run.awaitForTest(7000);
        assertFalse(run.isActive());
        assertTrue(cancelled.get());
    }

    @Test public void rejectsDuplicatesAndCancels() throws Exception {
        NativeRun run = new NativeRun();
        CountDownLatch started = new CountDownLatch(1);
        AtomicBoolean cancelled = new AtomicBoolean();
        assertTrue(run.start(() -> new ProcessBuilder("sh", "-c", "echo ready; exec sleep 30").start(), new NativeRun.Observer() {
            public void line(String line) { started.countDown(); }
            public void finished(int code, boolean wasCancelled) { cancelled.set(wasCancelled); }
        }));
        assertTrue(started.await(3, TimeUnit.SECONDS));
        assertFalse(run.start(() -> { throw new AssertionError("duplicate"); }, null));
        run.cancel();
        run.cancel();
        run.awaitForTest(7000);
        assertFalse(run.isActive());
        assertTrue(cancelled.get());
    }

    @Test public void failedStartReleasesOwnerAndAllowsRetry() throws Exception {
        NativeRun run = new NativeRun();
        AtomicInteger exit = new AtomicInteger();
        NativeRun.Observer observer = new NativeRun.Observer() {
            public void line(String line) {}
            public void finished(int code, boolean cancelled) { exit.set(code); }
        };
        assertTrue(run.start(() -> { throw new java.io.IOException("secret must not be logged"); }, observer));
        run.awaitForTest(3000);
        assertFalse(run.isActive());
        assertEquals(-1, exit.get());
        assertTrue(run.start(() -> new ProcessBuilder("sh", "-c", "exit 7").start(), observer));
        run.awaitForTest(3000);
        assertFalse(run.isActive());
        assertEquals(7, exit.get());
    }

    @Test public void outputOverflowKillsChild() throws Exception {
        NativeRun run = new NativeRun();
        AtomicInteger exit = new AtomicInteger();
        run.start(() -> new ProcessBuilder("sh", "-c", "head -c 131073 /dev/zero; exec sleep 30").start(), new NativeRun.Observer() {
            public void line(String line) { fail("oversized output accepted"); }
            public void finished(int code, boolean cancelled) { exit.set(code); }
        });
        run.awaitForTest(3000);
        assertFalse(run.isActive());
        assertEquals(-1, exit.get());
    }
}
