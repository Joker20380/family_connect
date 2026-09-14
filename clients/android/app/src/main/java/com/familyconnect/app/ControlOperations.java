package com.familyconnect.app;

import java.io.IOException;
import java.util.Objects;

/** Single process operation owner. A service lease survives between worker callbacks
 * and is released only after successful engine shutdown, including its destroy barrier.
 */
final class ControlOperations {
    static final ControlOperations APP = new ControlOperations();
    interface Mutation { void run() throws Exception; }
    static final class Stale extends IllegalStateException { Stale() { super("Stale VPN owner"); } }
    private Object session;
    void claim(Object owner) throws IOException {
        Objects.requireNonNull(owner);
        synchronized (ControlJournal.OWNER) {
            if (session != null && session != owner) throw new IOException("VPN cleanup still owns operations");
            session = owner;
        }
    }
    void session(Object owner, Runnable action) {
        synchronized (ControlJournal.OWNER) {
            if (owner == null || session != owner) throw new Stale();
            action.run();
        }
    }
    void release(Object owner) {
        synchronized (ControlJournal.OWNER) {
            if (owner == null || session != owner) throw new Stale();
            session = null;
        }
    }
    void requireOwner(Object owner) {
        synchronized(ControlJournal.OWNER) { if(owner==null||session!=owner)throw new Stale(); }
    }
    void requireIdle() throws IOException {
        synchronized (ControlJournal.OWNER) {
            if (session != null) throw new IOException("VPN session owns operations");
        }
    }
    void edit(Mutation recovery, Mutation action) throws Exception {
        synchronized (ControlJournal.OWNER) {
            if (session != null) throw new IOException("Disconnect VPN before changing profiles");
            recovery.run();
            requireIdle();
            action.run();
        }
    }
}
