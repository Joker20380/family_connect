package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static com.familyconnect.app.ControlJson.*;

/** Carrier-independent journal. Storage must atomically persist before returning.
 * All app mutations must share OWNER; encrypted OS storage is supplied separately.
 */
final class ControlJournal {
    static final Object OWNER = new Object();
    static final int LIMIT = 1024 * 1024;
    interface Storage {
        byte[] read() throws Exception;
        void create(byte[] raw) throws Exception; // Refuse all pre-existing state.
        void write(byte[] raw) throws Exception;  // Never create a missing store.
    }
    final Storage storage;
    final ControlIdentity identity;
    private final byte[] anchor;
    private final String clientVersion;
    private final boolean supportsAwg31;
    ControlJournal(Storage storage, ControlIdentity identity, byte[] anchor, String clientVersion) {
        this(storage,identity,anchor,clientVersion,false);
    }
    // Capability belongs to the application, never to mutable journal/network input.
    ControlJournal(Storage storage, ControlIdentity identity, byte[] anchor, String clientVersion, boolean supportsAwg31) {
        this.storage = storage; this.identity = identity; this.anchor = anchor.clone(); this.clientVersion = clientVersion;
        this.supportsAwg31 = supportsAwg31;
    }
    ControlProtocol.Verified verify(byte[] raw, long now) throws ControlProtocol.Rejected {
        return identity.verify(raw, anchor, clientVersion, now,supportsAwg31);
    }
    static byte[] encode(JsonObject record) { return record.toString().getBytes(StandardCharsets.UTF_8); }
    void initialize() throws Exception {
        synchronized (OWNER) {
            JsonObject r = new JsonObject(); r.addProperty("schema", 1); r.addProperty("device", identity.reference());
            r.addProperty("phase", "IDLE"); r.addProperty("floor", 0); r.addProperty("last_now", 0);
            for (String key : new String[]{"committed", "staged", "baseline", "result"}) r.add(key, JsonNull.INSTANCE);
            r.add("outbox", new JsonArray()); storage.create(encode(r));
        }
    }
    JsonObject read() throws Exception {
        byte[] raw = storage.read();
        try {
            require(raw.length <= LIMIT); JsonObject r = parse(raw).getAsJsonObject(); validate(r); return r;
        } finally { Arrays.fill(raw, (byte) 0); }
    }
    void save(JsonObject r) throws Exception {
        validate(r); byte[] raw = encode(r);
        try { if (raw.length > LIMIT) throw new IOException("Control journal too large"); storage.write(raw); }
        finally { Arrays.fill(raw, (byte) 0); }
    }
    private void validate(JsonObject r) throws Exception {
        long schema=integer(r.get("schema"),1);require(schema==1||schema==2);
        fields(r, "schema device committed staged phase baseline floor last_now outbox result"+(schema==2?" selected_gateway pending_gateway":""));
        require(text(r.get("device")).equals(identity.reference()));
        long floor = integer(r.get("floor"), 0), now = integer(r.get("last_now"), 0);
        String phase = text(r.get("phase"));
        boolean switching=phase.equals("SWITCHING");
        require(Arrays.asList("IDLE STAGED APPLYING APPLIED_PENDING ROLLING_BACK SWITCHING".split(" ")).contains(phase));
        if(switching)require(schema==2&&!r.get("committed").isJsonNull());
        if(schema==2) {
            require(switching!=r.get("pending_gateway").isJsonNull());
            for(String name:new String[]{"selected_gateway","pending_gateway"})if(!r.get(name).isJsonNull()) {
                String id=text(r.get(name));require(id.matches("[a-zA-Z0-9_-]{1,64}"));
                require(!r.get("committed").isJsonNull());
                boolean found=false;
                for(JsonElement p:unpack(r.getAsJsonObject("committed"),null).state().getAsJsonArray("transport_profiles"))
                    found|=id.equals(text(p.getAsJsonObject().get("gateway_id")));
                require(found);
            }
        }
        boolean idle = phase.equals("IDLE");
        require(idle == r.get("staged").isJsonNull() && idle == r.get("baseline").isJsonNull());
        if (!idle) require(r.get("baseline").isJsonObject());
        for (String name : new String[]{"committed", "staged"}) {
            if (r.get(name).isJsonNull()) continue;
            JsonObject entry = r.getAsJsonObject(name); ControlProtocol.Verified v = unpack(entry, null);
            long revision = integer(v.state().get("revision"), 1);
            require(revision <= floor && integer(entry.get("at"), 0) <= now);
            if (name.equals("staged")) require((switching||revision == floor) && entry.get("applied_at").isJsonNull() && entry.get("runtime").isJsonNull());
            else require(integer(entry.get("applied_at"), integer(entry.get("at"), 0)) <= now && entry.get("runtime").isJsonObject());
        }
        if(switching)require(r.getAsJsonObject("staged").get("envelope").equals(r.getAsJsonObject("committed").get("envelope")));
        if (!idle && !switching && !r.get("committed").isJsonNull())
            require(integer(unpack(r.getAsJsonObject("committed"), null).state().get("revision"), 1) < floor);
        require(r.get("outbox").isJsonArray() && r.getAsJsonArray("outbox").size() <= 64);
        Set<String> ids = new HashSet<>();
        for (JsonElement item : r.getAsJsonArray("outbox")) {
            JsonObject body = receipt(item); require(ids.add(text(body.get("ack_id"))));
            require(integer(body.get("sequence"), 0) <= floor && integer(body.get("timestamp"), 0) <= now);
        }
        if (!r.get("result").isJsonNull()) {
            JsonObject body = receipt(r.get("result"));
            require(integer(body.get("sequence"), 1) <= floor && integer(body.get("timestamp"), 0) <= now);
            require(Arrays.asList("COMMITTED", "ROLLED_BACK").contains(text(body.get("status"))));
        }
    }
    JsonObject receipt(JsonElement encoded) throws Exception {
        require(text(encoded).length() <= 5464);
        JsonObject body = ControlProtocol.verifyAck(ControlProtocol.base64(text(encoded), true));
        require(text(body.get("device")).equals(identity.reference())); return body;
    }
    ControlProtocol.Verified unpack(JsonObject entry, Long now) throws Exception {
        fields(entry, "envelope at digest applied_at runtime");
        require(text(entry.get("envelope")).length() <= 87384);
        long at = integer(entry.get("at"), 0);
        ControlProtocol.Verified verified = verify(ControlProtocol.base64(text(entry.get("envelope")), true), now == null ? at : now);
        require(verified.digest.equals(text(entry.get("digest")))); return verified;
    }
    static JsonObject pack(byte[] raw, ControlProtocol.Verified verified, long now) {
        JsonObject entry = new JsonObject(); entry.addProperty("envelope", Base64.getEncoder().encodeToString(raw));
        entry.addProperty("at", now); entry.addProperty("digest", verified.digest);
        entry.add("applied_at", JsonNull.INSTANCE); entry.add("runtime", JsonNull.INSTANCE); return entry;
    }
}
