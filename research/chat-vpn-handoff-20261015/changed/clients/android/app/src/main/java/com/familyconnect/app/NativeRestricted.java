package com.familyconnect.app;

import android.net.VpnService;

final class NativeRestricted {
    static void load() { System.loadLibrary("fc_restricted"); }
    static native long begin(String directory, String control, String resolver, long budgetMillis, VpnService protector);
    static native boolean attach(long handle, int tunFd);
    static native int state(long handle);
    static native String stats(long handle);
    static native String readiness(String directory);
    static native boolean validateDelivery(byte[] response, byte[] publicIdentity, byte[] anchor);
    static native int validationCode(byte[] response, byte[] publicIdentity, byte[] anchor);
    static native long beginReady(byte[] response, byte[] identity, byte[] anchor, String resolver, long budgetMillis, VpnService protector);
    static native boolean stop(long handle);
    static native long chatAcquire(byte[] response, byte[] identity, byte[] anchor, String resolver, Object protector);
    static native int chatState(long handle);
    static native void chatRelease(long handle);
    static native int chatOpen(long handle, int timeoutMillis);
    static native String chatRequest(long handle, String path, String body, int timeoutMillis);
}
