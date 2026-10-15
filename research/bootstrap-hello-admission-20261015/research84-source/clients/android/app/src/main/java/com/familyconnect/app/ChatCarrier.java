package com.familyconnect.app;

import android.content.Context;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.util.Arrays;

public final class ChatCarrier implements AutoCloseable {
    private final Context context;
    private final ChatNetworkAndroid underlay;
    private long handle;
    private boolean closed;
    private volatile String route = "DIRECT";

    ChatCarrier(Context context) {
        this.context = context.getApplicationContext();
        underlay = new ChatNetworkAndroid(context);
    }

    private synchronized long acquire() throws Exception {
        if (closed) throw new IOException("chat_closed");
        NativeRestricted.load();
        if (handle != 0 && NativeRestricted.chatState(handle) < 0) {
            NativeRestricted.chatRelease(handle); handle = 0;
        }
        if (handle == 0) {
            try (ControlIdentity identity = new FriendsIdentityVault(context).load()) {
                byte[] anchor = ControlTrust.anchor(context);
                byte[] publicIdentity = identity.publicIdentity();
                RestrictedCache cache = new RestrictedCache(new RestrictedVault(context),
                    raw -> NativeRestricted.validateDelivery(raw, publicIdentity, anchor));
                byte[] response;
                synchronized (RestrictedVault.LOCK) { response = cache.usable(); }
                if (response == null) throw new IOException("bootstrap_unavailable");
                byte[] material = identity.material();
                byte[] secret = Arrays.copyOf(material, 64);
                try { handle = NativeRestricted.chatAcquire(response, secret, anchor, "1.1.1.1:53", underlay); }
                finally { Arrays.fill(material, (byte)0); Arrays.fill(secret, (byte)0); Arrays.fill(response, (byte)0); }
                if (handle == 0) throw new IOException("bootstrap_rejected");
            }
        }
        return handle;
    }

    public boolean bindSocket(int descriptor) { return !closed && underlay.bindSocket(descriptor); }

    public int openMailbox(int timeoutMillis) {
        try {
            long lease = acquire();
            int descriptor = NativeRestricted.chatOpen(lease, Math.min(30000, timeoutMillis));
            if (descriptor >= 0) route = NativeRestricted.chatState(lease) == 2 ? "EXISTING_EXIT" : "SERVICE_ONLY";
            return descriptor;
        } catch (Exception | LinkageError unavailable) { return -1; }
    }

    JsonObject request(String path, String body, int timeoutMillis) throws Exception {
        long lease = acquire();
        String raw = NativeRestricted.chatRequest(lease, path, body, Math.min(30000, timeoutMillis));
        if (raw == null) throw new IOException("carrier_unavailable");
        JsonObject result = JsonParser.parseString(raw).getAsJsonObject();
        if (result.has("error")) {
            if ("denied".equals(result.get("error").getAsString())) throw new FriendsAccessAndroid.Denied();
            throw new IOException("carrier_unavailable");
        }
        route = NativeRestricted.chatState(lease) == 2 ? "EXISTING_EXIT" : "SERVICE_ONLY";
        int status = result.get("status").getAsInt();
        if (status == 409) throw new FriendsAccessAndroid.Conflict();
        if (status == 400 || status == 401 || status == 403) throw new FriendsAccessAndroid.Denied();
        if (status != 200) throw new IOException("chat_api_unavailable");
        return ControlJson.parse(result.get("body").getAsString().getBytes(java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
    }

    String route() { return route; }

    @Override public synchronized void close() {
        closed = true;
        if (handle != 0) { NativeRestricted.chatRelease(handle); handle = 0; }
    }
}
