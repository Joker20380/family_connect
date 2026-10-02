package com.familyconnect.app;

import android.net.VpnService;

final class NativeRestricted {
    static void load() { System.loadLibrary("fc_restricted"); }
    static native long begin(String directory, String control, String resolver, VpnService protector);
    static native boolean attach(long handle, int tunFd);
    static native int state(long handle);
    static native String stats(long handle);
    static native String readiness(String directory);
    static native boolean validateDelivery(byte[] response, byte[] publicIdentity, byte[] anchor);
    static native int validationCode(byte[] response, byte[] publicIdentity, byte[] anchor);
    static native long beginReady(byte[] response, byte[] identity, byte[] anchor, String resolver, VpnService protector);
    static native boolean stop(long handle);
}
