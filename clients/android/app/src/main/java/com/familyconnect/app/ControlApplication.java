package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;
import java.nio.charset.StandardCharsets;
import static com.familyconnect.app.ControlJson.*;

/** Native profile transaction policy. Host uses the existing service worker and engine. */
final class ControlApplication implements ControlTransaction.Resumable {
    interface Host {
        JsonObject capture() throws Exception;
        void validate(String transport, String profile) throws Exception;
        void stop() throws Exception;
        void save(String transport, String profile) throws Exception; // null removes this fixed slot.
        void start(String transport, long expiresAt) throws Exception;
        boolean healthy() throws Exception;
        boolean cancelled();
    }
    private final Host host;
    private final ControlIdentity identity;
    private final java.util.function.Supplier<String> gateway;
    private static final List<String> SLOTS = Arrays.asList("wg", "awg", "tcp");
    ControlApplication(Host host, ControlIdentity identity) { this(host,identity,()->""); }
    ControlApplication(Host host, ControlIdentity identity, java.util.function.Supplier<String> gateway) {
        this.host=host; this.identity=identity; this.gateway=gateway;
    }
    private String selectedSlot(ControlProtocol.Verified config) throws IOException {
        String wanted=gateway.get();
        for(JsonElement item:config.state().getAsJsonArray("transport_profiles")) {
            JsonObject profile=item.getAsJsonObject();
            if(wanted.isEmpty()||wanted.equals(text(profile.get("gateway_id")))) {
                String transport=text(profile.get("transport"));
                return transport.equals("wireguard")?"wg":transport.equals("amneziawg")?"awg":"tcp";
            }
        }
        throw new IOException("Selected gateway is not in signed configuration");
    }
    private JsonObject checked(JsonObject value) throws Exception {
        fields(value, "schema profiles active lease"); require(integer(value.get("schema"),1)==1);
        integer(value.get("lease"),0); JsonObject profiles=value.getAsJsonObject("profiles"); fields(profiles,"wg awg tcp");
        for(String slot:SLOTS) if(!profiles.get(slot).isJsonNull()) {
            String profile=text(profiles.get(slot));require(profile.getBytes(StandardCharsets.UTF_8).length<=16384);
            host.validate(slot,profile);
        }
        if(!value.get("active").isJsonNull()) {
            String slot=text(value.get("active"));require(SLOTS.contains(slot)&&!profiles.get(slot).isJsonNull());
        } else require(integer(value.get("lease"),0)==0);
        return value.deepCopy();
    }
    public JsonObject snapshot(JsonObject previousRuntime) throws Exception { return checked(host.capture()); }
    private LinkedHashMap<String,String> materialize(ControlProtocol.Verified verified) throws Exception {
        LinkedHashMap<String,String> profiles=new LinkedHashMap<>();
        byte[] key=identity.wireguardPrivateKey();
        try {
            for(JsonElement item:verified.state().getAsJsonArray("transport_profiles")) {
                JsonObject p=item.getAsJsonObject();String transport=text(p.get("transport"));
                String slot=transport.equals("wireguard")?"wg":transport.equals("amneziawg")?"awg":"tcp";
                if(profiles.containsKey(slot))throw new IOException("Multiple signed profiles for one native slot");
                String raw=text(p.get("config"));
                if(!slot.equals("tcp"))raw=raw.replace("LOCAL_DEVICE_KEY",Base64.getEncoder().encodeToString(key));
                host.validate(slot,raw);profiles.put(slot,raw);
            }
        } finally {Arrays.fill(key,(byte)0);}
        if(profiles.isEmpty())throw new IOException("No native profile");return profiles;
    }
    public void apply(ControlProtocol.Verified config, JsonObject baseline) throws Exception {
        checked(baseline);LinkedHashMap<String,String> profiles=materialize(config);String selected=selectedSlot(config);
        if(host.cancelled())throw new IOException("Control operation cancelled");
        host.stop();
        for(var entry:profiles.entrySet()) {
            if(host.cancelled())throw new IOException("Control operation cancelled");
            host.save(entry.getKey(),entry.getValue());
        }
        if(host.cancelled())throw new IOException("Control operation cancelled");
        host.start(selected,integer(config.state().get("expires_at"),1));
    }
    public void resume(ControlProtocol.Verified config) throws Exception {
        JsonObject saved=checked(host.capture());
        if(!saved.get("active").isJsonNull())throw new IOException("Resume requires stopped VPN");
        LinkedHashMap<String,String> profiles=materialize(config);String selected=selectedSlot(config);
        for(var entry:profiles.entrySet()) {
            JsonElement stored=saved.getAsJsonObject("profiles").get(entry.getKey());
            if(stored.isJsonNull()||!entry.getValue().equals(text(stored)))
                throw new IOException("Committed profile differs from local slot");
        }
        if(host.cancelled())throw new IOException("Control operation cancelled");
        host.start(selected,integer(config.state().get("expires_at"),1));
        if(host.cancelled())throw new IOException("Control operation cancelled");
    }
    public void stopResume() throws Exception {host.stop();}
    public boolean healthy(ControlProtocol.Verified config) throws Exception { return !host.cancelled()&&host.healthy()&&!host.cancelled(); }
    public void rollback(ControlProtocol.Verified candidate, ControlProtocol.Verified previous,
                         JsonObject baseline, boolean mayRestore) throws Exception {
        // Stop first even if a snapshot is corrupt: never leave an uncommitted candidate running.
        host.stop();JsonObject saved=checked(baseline);JsonObject profiles=saved.getAsJsonObject("profiles");
        for(String slot:SLOTS)host.save(slot,profiles.get(slot).isJsonNull()?null:text(profiles.get(slot)));
        if(mayRestore&&!host.cancelled()&&!saved.get("active").isJsonNull()) {
            long lease=integer(saved.get("lease"),0);
            if(previous!=null)lease=integer(previous.state().get("expires_at"),1);
            host.start(text(saved.get("active")),lease);
        }
    }
}
