package com.familyconnect.app;

import android.content.Context;

final class ProvisioningTestGate {
    static Permit enter(Context context) { return new Permit(); }
    static final class Permit implements AutoCloseable {
        boolean blocked() { return false; }
        void requireAvailable() throws FriendsReadinessProtocol.Unavailable {}
        public void close() {}
    }
}
