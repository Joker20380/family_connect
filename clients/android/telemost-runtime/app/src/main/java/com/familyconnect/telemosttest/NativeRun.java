package com.familyconnect.telemosttest;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

final class NativeRun {
    interface Factory { Process create() throws Exception; }
    interface Observer { void line(String line); void finished(int code, boolean cancelled); }
    private boolean active;
    private boolean cancelled;
    private Process process;
    private Thread worker;

    synchronized boolean start(Factory factory, Observer observer) {
        if (active) return false;
        active = true;
        cancelled = false;
        worker = new Thread(() -> execute(factory, observer), "telemost-native-owner");
        worker.start();
        return true;
    }

    private void execute(Factory factory, Observer observer) {
        int code = -1;
        Process child = null;
        try {
            synchronized (this) {
                if (cancelled) return;
            }
            child = factory.create();
            synchronized (this) {
                process = child;
                if (cancelled) terminate(child);
            }
            try (InputStream output = child.getInputStream()) {
                ByteArrayOutputStream line = new ByteArrayOutputStream();
                int value;
                while ((value = output.read()) != -1) {
                    if (value == '\n') {
                        observer.line(new String(line.toByteArray(), StandardCharsets.UTF_8));
                        line.reset();
                    } else {
                        if (line.size() >= 128 * 1024) throw new IllegalStateException("output limit");
                        line.write(value);
                    }
                }
            }
            code = child.waitFor();
        } catch (Exception ignored) {
            code = -1;
        } finally {
            if (child != null) {
                try {
                    if (child.isAlive()) {
                        child.destroy();
                        if (!child.waitFor(5, java.util.concurrent.TimeUnit.SECONDS)) child.destroyForcibly();
                    }
                    child.waitFor();
                    synchronized (this) { if (cancelled) code = child.exitValue(); }
                } catch (InterruptedException ignored) {
                    child.destroyForcibly();
                    Thread.currentThread().interrupt();
                }
            }
            synchronized (this) {
                process = null;
                observer.finished(code, cancelled);
                active = false;
                notifyAll();
            }
        }
    }

    synchronized boolean isActive() { return active; }

    synchronized void cancel() {
        if (cancelled) return;
        cancelled = true;
        Process child = process;
        if (child == null) return;
        terminate(child);
    }

    private static void terminate(Process child) {
        child.destroy();
        new Thread(() -> {
            try {
                if (!child.waitFor(5, java.util.concurrent.TimeUnit.SECONDS)) child.destroyForcibly();
            } catch (InterruptedException ignored) {
                child.destroyForcibly();
                Thread.currentThread().interrupt();
            }
        }, "telemost-native-reaper").start();
    }

    void awaitForTest(long millis) throws InterruptedException {
        Thread current;
        synchronized (this) { current = worker; }
        if (current != null) current.join(millis);
    }
}
