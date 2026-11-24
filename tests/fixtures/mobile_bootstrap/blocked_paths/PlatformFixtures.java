package com.familyconnect.app;

import android.content.Context;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Arrays;
import javax.net.ssl.HttpsURLConnection;

final class ConnectionService {
    static String status = "off", healthStatus = "off";
}

final class ChatNetworkAndroid {
    ChatNetworkAndroid(Context context) {}
    HttpsURLConnection openHttps(String address, ReadinessFetchTrace trace) throws Exception {
        if (trace != null) trace.network("CELLULAR", 1);
        return (HttpsURLConnection) new java.net.URL(address).openConnection();
    }
    boolean bindSocket(int descriptor) { throw new AssertionError("No native socket expected"); }
}

final class ControlRnsAndroid {
    static int opens;
    ControlRnsAndroid(Context context, long deadline) {}
    void openReadiness(ReadinessFetchTrace trace) throws FriendsReadinessProtocol.Unavailable {
        opens++;
        throw new FriendsReadinessProtocol.Unavailable();
    }
    byte[] requestReadiness(String path, byte[] raw) { throw new AssertionError("Relay must not open"); }
    void cancel() {}
    void close() {}
}

final class FriendsIdentityVault {
    static byte[] saved;
    static int creates;
    FriendsIdentityVault(Context context) {}
    ControlIdentity create() {
        if (saved != null) throw new AssertionError("Unexpected identity replacement");
        ControlIdentity identity = ControlIdentity.generate();
        saved = identity.material();
        creates++;
        return identity;
    }
    ControlIdentity load() throws IOException {
        if (saved == null) throw new IOException("Synthetic identity absent");
        return ControlIdentity.restore(saved);
    }
    static void reset() {
        if (saved != null) Arrays.fill(saved, (byte) 0);
        saved = null;
        creates = 0;
    }
}

final class FriendsConfigurationVault {
    FriendsConfigurationVault(Context context) {}
    FriendsConfigurationVault(Context context, boolean explicit) {}
    byte[] read() { throw new AssertionError("Normal profiles outside this test"); }
    void create(byte[] raw) { throw new AssertionError("Normal profiles outside this test"); }
    void write(byte[] raw) { throw new AssertionError("Normal profiles outside this test"); }
}

final class FriendsRestricted {
    static void prewarm(Context context) { throw new AssertionError("Unexpected profile success"); }
}

final class ControlTrust {
    static byte[] anchor(Context context) { return new byte[32]; }
}

final class RestrictedVault implements RestrictedCache.Storage {
    static final Object LOCK = new Object();
    RestrictedVault(Context context) {}
    public byte[] read() { return null; }
    public void write(byte[] raw) { throw new AssertionError("Chat cannot provision missing readiness"); }
}

final class NativeRestricted {
    static int acquisitions;
    static void load() {}
    static boolean validateDelivery(byte[] raw, byte[] identity, byte[] anchor) { throw new AssertionError("Missing cache cannot reach validation"); }
    static long chatAcquire(byte[] raw, byte[] identity, byte[] anchor, String resolver, ChatNetworkAndroid network) {
        acquisitions++;
        throw new AssertionError("Missing cache cannot reach native carrier");
    }
    static int chatState(long handle) { throw new AssertionError(); }
    static void chatRelease(long handle) { throw new AssertionError(); }
    static int chatOpen(long handle, int timeout) { throw new AssertionError(); }
    static String chatRequest(long handle, String path, String body, int timeout) { throw new AssertionError(); }
}

final class BuildConfig {
    static final String VERSION_NAME = "isolated-test";
    static final int VERSION_CODE = 113;
}

final class DeviceSupport {
    static void store(Context context, String device, String support) { throw new AssertionError(); }
}

final class ChatLocalAndroid {
    com.google.gson.JsonElement call(String method, JsonObject args) { throw new AssertionError(); }
    JsonObject enrollmentProof(String device, String nonce) { throw new AssertionError(); }
}
