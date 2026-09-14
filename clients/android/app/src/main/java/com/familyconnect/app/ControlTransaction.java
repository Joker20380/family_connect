package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;
import java.util.function.LongSupplier;
import static com.familyconnect.app.ControlJson.*;

/** Durable state machine; Application must use the existing service lifecycle, not a second VPN. */
final class ControlTransaction {
    interface Application {
        JsonObject snapshot(JsonObject previousRuntime) throws Exception; // Read-only, bounded, no side effects.
        void apply(ControlProtocol.Verified config, JsonObject baseline) throws Exception;
        boolean healthy(ControlProtocol.Verified config) throws Exception;
        void rollback(ControlProtocol.Verified candidate, ControlProtocol.Verified previous,
                      JsonObject baseline, boolean mayRestore) throws Exception; // Idempotent; always clean candidate.
    }
    interface Resumable extends Application {
        void resume(ControlProtocol.Verified config) throws Exception; // No persistent mutations.
        void stopResume() throws Exception;
    }
    interface Sender { boolean send(byte[] acknowledgement) throws Exception; }
    interface Mutation { void run() throws Exception; }
    private final ControlJournal journal;
    private final Application application;
    private final LongSupplier clock;
    private final Object serviceOwner;
    ControlTransaction(ControlJournal journal, Application application, LongSupplier clock) {
        this(journal,application,clock,null);
    }
    ControlTransaction(ControlJournal journal, Application application, LongSupplier clock, Object serviceOwner) {
        this.journal=journal;this.application=application;this.clock=clock;this.serviceOwner=serviceOwner;
    }
    private void admitted() throws IOException {
        if(serviceOwner==null)ControlOperations.APP.requireIdle();else ControlOperations.APP.requireOwner(serviceOwner);
    }
    private long time(JsonObject r) throws ControlProtocol.Rejected {
        long now = clock.getAsLong();
        if (now < integer(r.get("last_now"), 0)) throw new ControlProtocol.Rejected("CLOCK");
        r.addProperty("last_now", now); return now;
    }
    private String ack(JsonObject r, String digest, ControlProtocol.Verified verified,
                       String status, String error, long now, boolean terminal) throws Exception {
        JsonArray outbox = r.getAsJsonArray("outbox");
        for (JsonElement existing : outbox) {
            JsonObject body = journal.receipt(existing);
            if (text(body.get("envelope_hash")).equals(digest) && text(body.get("status")).equals(status) && text(body.get("error")).equals(error)) {
                if (terminal) r.add("result", existing.deepCopy()); return status;
            }
        }
        if (outbox.size() >= 64) throw new IOException("Control ACK outbox full");
        JsonObject state = verified == null ? null : verified.state();
        byte[] raw = journal.identity.acknowledgement(digest, state == null ? null : text(state.get("config_id")),
            state == null ? 0 : integer(state.get("revision"), 1), status, error, now);
        JsonElement encoded = new JsonPrimitive(Base64.getEncoder().encodeToString(raw));
        outbox.add(encoded); if (terminal) r.add("result", encoded.deepCopy()); return status;
    }
    private String rollback(JsonObject r, String error) throws Exception {
        long now = time(r); ControlProtocol.Verified candidate = journal.unpack(r.getAsJsonObject("staged"), null);
        r.addProperty("phase", "ROLLING_BACK"); journal.save(r);
        try {
            ControlProtocol.Verified previous = null; boolean mayRestore = true;
            if (!r.get("committed").isJsonNull()) {
                try { previous = journal.unpack(r.getAsJsonObject("committed"), now); }
                catch (ControlProtocol.Rejected expired) { mayRestore = false; }
            }
            application.rollback(candidate, previous, r.getAsJsonObject("baseline").deepCopy(), mayRestore);
        } catch (Exception failure) {
            ack(r, candidate.digest, candidate, "FAILED", "ROLLBACK", now, false); journal.save(r); return "FAILED";
        }
        r.addProperty("phase", "IDLE"); r.add("staged", JsonNull.INSTANCE); r.add("baseline", JsonNull.INSTANCE);
        ack(r, candidate.digest, candidate, "ROLLED_BACK", error, now, true); journal.save(r); return "ROLLED_BACK";
    }
    String recover() throws Exception {
        synchronized (ControlJournal.OWNER) {
            admitted();
            JsonObject r = journal.read(); time(r);
            if (!r.get("staged").isJsonNull()) return rollback(r, "RECOVERY");
            journal.save(r); return "IDLE";
        }
    }
    /** Explicit reconnect of an already committed configuration; never replay receive(). */
    String resume() throws Exception {
        synchronized(ControlJournal.OWNER) {
            admitted();
            JsonObject r=journal.read();long now=time(r);
            if(!r.get("staged").isJsonNull())throw new IOException("Control recovery required");
            if(r.get("committed").isJsonNull()){journal.save(r);return "IDLE";}
            ControlProtocol.Verified config=journal.unpack(r.getAsJsonObject("committed"),now);
            if(!(application instanceof Resumable))throw new IOException("Resume unsupported");
            Resumable nativeApp=(Resumable)application;
            // Persist the clock floor before any activation. No profile writes or new ACKs.
            journal.save(r);
            try {
                nativeApp.resume(config);
                if(!nativeApp.healthy(config))throw new IOException("Resume health failed");
                journal.unpack(r.getAsJsonObject("committed"),time(r));
                journal.save(r);
                return "RESUMED";
            } catch(Exception|LinkageError failure) {
                try{nativeApp.stopResume();}catch(Exception|LinkageError cleanup){failure.addSuppressed(cleanup);}
                throw failure;
            }
        }
    }
    // Future Activity/service adapters must enter here rather than mutate ProfileStore independently.
    void manual(Mutation action) throws Exception {
        synchronized (ControlJournal.OWNER) {
            if (recover().equals("FAILED")) throw new IOException("Control recovery required");
            action.run();
        }
    }
    String receive(byte[] input) throws Exception {
        if (input == null || input.length > 65536) throw new ControlProtocol.Rejected("SIZE");
        byte[] raw = input.clone(); // Caller/carrier cannot replace bytes after verification.
        synchronized (ControlJournal.OWNER) {
            admitted();
            JsonObject r = journal.read();
            if (!r.get("staged").isJsonNull() && rollback(r, "RECOVERY").equals("FAILED")) return "FAILED";
            long now = time(r);
            if (r.getAsJsonArray("outbox").size() > 58) throw new IOException("Control ACK outbox requires delivery");
            String digest = ControlProtocol.hash(raw); ControlProtocol.Verified verified;
            try {
                verified = journal.verify(raw, now);
                if (!r.get("result").isJsonNull()) {
                    JsonObject result = journal.receipt(r.get("result"));
                    if (text(result.get("envelope_hash")).equals(digest)) {
                        if (!r.getAsJsonArray("outbox").contains(r.get("result"))) r.getAsJsonArray("outbox").add(r.get("result").deepCopy());
                        journal.save(r); return text(result.get("status"));
                    }
                }
                if (!r.get("committed").isJsonNull() && text(r.getAsJsonObject("committed").get("digest")).equals(digest)) {
                    ack(r, digest, verified, "COMMITTED", "NONE", now, false); journal.save(r); return "COMMITTED";
                }
                if (integer(verified.state().get("revision"), 1) <= integer(r.get("floor"), 0)) throw new ControlProtocol.Rejected("REPLAY");
                JsonElement previous = r.get("committed").isJsonNull() ? JsonNull.INSTANCE : r.getAsJsonObject("committed").get("digest");
                if (!verified.state().get("previous_config_hash").equals(previous)) throw new ControlProtocol.Rejected("PREVIOUS_HASH");
            } catch (ControlProtocol.Rejected rejected) {
                ack(r, digest, null, "REJECTED", rejected.category, now, false); journal.save(r); return "REJECTED";
            }
            JsonObject prior = r.get("committed").isJsonNull() ? null : r.getAsJsonObject("committed").getAsJsonObject("runtime").deepCopy();
            JsonObject baseline = Objects.requireNonNull(application.snapshot(prior)).deepCopy();
            r.add("staged", ControlJournal.pack(raw, verified, now)); r.add("baseline", baseline);
            r.addProperty("phase", "STAGED"); r.addProperty("floor", integer(verified.state().get("revision"), 1));
            ack(r, digest, verified, "RECEIVED", "NONE", now, false); journal.save(r);
            r.addProperty("phase", "APPLYING"); journal.save(r);
            try { application.apply(verified, baseline.deepCopy()); }
            catch (Exception failure) { return rollback(r, "APPLY"); }
            r.addProperty("phase", "APPLIED_PENDING");
            ack(r, digest, verified, "APPLIED", "NONE", time(r), false); journal.save(r);
            boolean healthy;
            try { healthy = application.healthy(verified); journal.verify(raw, time(r)); }
            catch (Exception failure) { healthy = false; }
            if (!healthy) return rollback(r, "HEALTH");
            JsonObject runtime = Objects.requireNonNull(application.snapshot(null)).deepCopy();
            // A slow final snapshot must not turn an expired lease into a new commit.
            try { journal.verify(raw, time(r)); }
            catch (ControlProtocol.Rejected expired) { return rollback(r, "HEALTH"); }
            JsonObject committed = r.getAsJsonObject("staged").deepCopy();
            committed.addProperty("applied_at", integer(r.get("last_now"), 0));
            committed.add("runtime", runtime);
            r.add("committed", committed); r.add("staged", JsonNull.INSTANCE); r.add("baseline", JsonNull.INSTANCE); r.addProperty("phase", "IDLE");
            ack(r, digest, verified, "COMMITTED", "NONE", integer(r.get("last_now"), 0), true);
            journal.save(r); return "COMMITTED";
        }
    }
    boolean flush(Sender sender) throws Exception {
        // Bounded batch snapshot. No network wait holds the application owner.
        List<String> pending = new ArrayList<>();
        synchronized (ControlJournal.OWNER) {
            for (JsonElement item : journal.read().getAsJsonArray("outbox")) pending.add(text(item));
        }
        for (String encoded : pending) {
            try { if (!sender.send(ControlProtocol.base64(encoded, true))) return false; }
            catch (Exception unavailable) { return false; }
            synchronized (ControlJournal.OWNER) {
                JsonObject latest = journal.read(); JsonArray outbox = latest.getAsJsonArray("outbox");
                // Remove only the exact durably acknowledged bytes, preserving concurrent new events.
                if (outbox.remove(new JsonPrimitive(encoded))) journal.save(latest);
            }
        }
        synchronized (ControlJournal.OWNER) { return journal.read().getAsJsonArray("outbox").isEmpty(); }
    }
}
