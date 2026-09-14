package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.*;
import javax.crypto.KeyGenerator;

public class ControlTransactionTest {
    static byte[] resource(String name) throws Exception {
        try (var input = ControlTransactionTest.class.getClassLoader().getResourceAsStream("control-v1/"+name)) { return input.readAllBytes(); }
    }
    static final class Death extends Error { }
    static final class Memory implements ControlJournal.Storage {
        byte[] raw; int writes, failAt = -1; boolean after;
        public byte[] read() throws Exception { if (raw == null) throw new IOException("Missing store"); return raw.clone(); }
        public void create(byte[] bytes) throws Exception { if (raw != null) throw new IOException("Already enrolled"); raw = bytes.clone(); }
        public void write(byte[] bytes) {
            writes++; if (writes == failAt && !after) throw new Death();
            raw = bytes.clone(); if (writes == failAt && after) throw new Death();
        }
    }
    static final class App implements ControlTransaction.Application {
        int applies, rollbacks, snapshots; boolean healthy = true, failApply, failRollback, crashApply, restore; long[] clock;
        long healthTime, snapshotTime; JsonObject runtime = new JsonObject();
        public JsonObject snapshot(JsonObject prior) { snapshots++; if (snapshots == 2 && snapshotTime != 0) clock[0] = snapshotTime; return runtime.deepCopy(); }
        public void apply(ControlProtocol.Verified config, JsonObject baseline) throws Exception {
            applies++; runtime.addProperty("candidate", config.digest);
            if (crashApply) throw new Death(); if (failApply) throw new IOException("Apply failed");
        }
        public boolean healthy(ControlProtocol.Verified config) { if (healthTime != 0) clock[0] = healthTime; return healthy; }
        public void rollback(ControlProtocol.Verified candidate, ControlProtocol.Verified previous, JsonObject baseline, boolean mayRestore) throws Exception {
            rollbacks++; restore = mayRestore;
            if (failRollback) throw new IOException("Cleanup failed");
            runtime = mayRestore ? baseline.deepCopy() : new JsonObject();
        }
    }
    static final class Harness implements AutoCloseable {
        final Memory store = new Memory(); final App app = new App(); final long[] clock = {1000};
        final ControlIdentity identity; final byte[] anchor; ControlJournal journal; ControlTransaction core;
        Harness() throws Exception {
            JsonObject f = ControlJson.parse(resource("TEST-ONLY-identity.json")).getAsJsonObject();
            byte[] material = new byte[96];
            System.arraycopy(ControlProtocol.base64(f.get("rns_private_b64").getAsString(), true), 0, material, 0, 64);
            System.arraycopy(ControlProtocol.base64(f.get("wg_private_b64").getAsString(), true), 0, material, 64, 32);
            identity = ControlIdentity.restore(material); Arrays.fill(material, (byte) 0);
            anchor = ControlProtocol.base64(f.get("anchor_b64").getAsString(), true); app.clock = clock;
            restart(); journal.initialize();
        }
        void restart() { journal = new ControlJournal(store, identity, anchor, "0.2.9"); core = new ControlTransaction(journal, app, () -> clock[0]); }
        String receive(String name) throws Exception { return core.receive(resource(name+".envelope")); }
        JsonObject state() throws Exception { return journal.read(); }
        public void close() { identity.close(); }
    }
    @Test public void commitDuplicateAndReplay() throws Exception {
        try (Harness h = new Harness()) {
            assertEquals("COMMITTED", h.receive("valid-wg")); assertEquals(1, h.app.applies);
            assertEquals(3, h.state().getAsJsonArray("outbox").size());
            h.restart(); assertEquals("IDLE", h.core.recover());
            assertEquals("COMMITTED", h.receive("valid-wg")); assertEquals(1, h.app.applies);
            assertEquals("REJECTED", h.receive("same-revision-other-bytes"));
            assertEquals("REPLAY", lastAck(h).get("error").getAsString());
            assertEquals("REJECTED", h.receive("wrong-previous"));
            assertEquals("PREVIOUS_HASH", lastAck(h).get("error").getAsString());
            assertEquals("COMMITTED", h.receive("valid-next")); assertEquals(2, h.app.applies);
            assertEquals(2, h.state().get("floor").getAsLong());
        }
    }
    static JsonObject lastAck(Harness h) throws Exception {
        JsonArray a = h.state().getAsJsonArray("outbox"); return h.journal.receipt(a.get(a.size()-1));
    }
    @Test public void crashAtEveryPersistBoundary() throws Exception {
        for (boolean after : new boolean[]{false, true}) for (int boundary = 1; boundary <= 4; boundary++) {
            try (Harness h = new Harness()) {
                h.store.failAt = boundary; h.store.after = after;
                assertThrows(Death.class, () -> h.receive("valid-wg"));
                h.store.failAt = -1; h.restart(); String result = h.core.recover();
                boolean committed = after && boundary == 4, untouched = !after && boundary == 1;
                assertEquals(committed || untouched ? "IDLE" : "ROLLED_BACK", result);
                assertEquals(untouched ? 0 : 1, h.state().get("floor").getAsLong());
                assertEquals(committed || untouched ? 0 : 1, h.app.rollbacks);
                int applies = h.app.applies;
                if (!untouched) { assertEquals(committed ? "COMMITTED" : "ROLLED_BACK", h.receive("valid-wg")); assertEquals(applies, h.app.applies); }
            }
        }
    }
    @Test public void interruptedAndFailedRollbackGateManualMutations() throws Exception {
        try (Harness h = new Harness()) {
            h.app.crashApply = true; assertThrows(Death.class, () -> h.receive("valid-wg"));
            h.restart(); h.app.failRollback = true;
            assertEquals("FAILED", h.core.recover()); assertEquals("ROLLING_BACK", h.state().get("phase").getAsString());
            int[] mutations = {0}; assertThrows(IOException.class, () -> h.core.manual(() -> mutations[0]++));
            assertEquals(0, mutations[0]); assertEquals("FAILED", h.receive("valid-next")); assertEquals(1, h.app.applies);
            h.app.failRollback = false; h.core.manual(() -> mutations[0]++);
            assertEquals(1, mutations[0]); assertEquals("IDLE", h.state().get("phase").getAsString());
            assertEquals(1, h.state().get("floor").getAsLong());
        }
    }
    @Test public void rollbackCrashesRemainRecoverable() throws Exception {
        for (int boundary : new int[]{3,4}) for (boolean after : new boolean[]{false,true}) {
            try (Harness h = new Harness()) {
                h.app.failApply = true; h.store.failAt = boundary; h.store.after = after;
                assertThrows(Death.class, () -> h.receive("valid-wg")); h.store.failAt = -1; h.restart();
                assertEquals(after && boundary == 4 ? "IDLE" : "ROLLED_BACK", h.core.recover());
                assertEquals(1, h.state().get("floor").getAsLong());
                assertEquals("ROLLED_BACK", h.receive("valid-wg")); assertEquals(1, h.app.applies);
            }
        }
    }
    @Test public void failedHealthAndLeaseExpiryCannotCommitOrRestoreExpiredConfig() throws Exception {
        try (Harness h = new Harness()) {
            h.app.healthy = false; assertEquals("ROLLED_BACK", h.receive("valid-wg"));
            assertEquals("HEALTH", lastAck(h).get("error").getAsString()); assertTrue(h.state().get("committed").isJsonNull());
        }
        try (Harness h = new Harness()) {
            assertEquals("COMMITTED", h.receive("valid-wg"));
            h.app.healthTime = 4600; assertEquals("ROLLED_BACK", h.receive("valid-next"));
            assertFalse(h.app.restore); assertEquals(2, h.state().get("floor").getAsLong());
            assertEquals("REJECTED", h.receive("valid-wg")); assertEquals("LEASE", lastAck(h).get("error").getAsString());
        }
    }
    @Test public void slowFinalSnapshotCannotCommitAnExpiredLease() throws Exception {
        try (Harness h = new Harness()) {
            h.app.snapshotTime = 4600;
            assertEquals("ROLLED_BACK", h.receive("valid-wg"));
            assertTrue(h.state().get("committed").isJsonNull());
            assertEquals("HEALTH", lastAck(h).get("error").getAsString());
        }
    }
    @Test public void clockRollbackDoesNotMutate() throws Exception {
        try (Harness h = new Harness()) {
            h.receive("valid-wg"); byte[] previous = h.store.raw.clone(); h.clock[0] = 999;
            assertThrows(ControlProtocol.Rejected.class, h.core::recover); assertArrayEquals(previous, h.store.raw);
            assertThrows(ControlProtocol.Rejected.class, () -> h.receive("valid-next")); assertEquals(1, h.app.applies);
        }
    }
    @Test public void carrierFailureRetainsExactReceiptsAndDuplicateRequeuesResult() throws Exception {
        try (Harness h = new Harness()) {
            h.receive("valid-wg"); byte[] previous = h.store.raw.clone();
            assertFalse(h.core.flush(raw -> { throw new IOException("offline"); })); assertArrayEquals(previous, h.store.raw);
            List<byte[]> first = new ArrayList<>(); int[] attempt = {0};
            assertFalse(h.core.flush(raw -> { first.add(raw.clone()); return ++attempt[0] < 2; }));
            h.restart(); List<byte[]> retry = new ArrayList<>(); assertTrue(h.core.flush(raw -> { retry.add(raw.clone()); return true; }));
            assertArrayEquals(first.get(1), retry.get(0)); assertEquals(0, h.state().getAsJsonArray("outbox").size());
            assertEquals("COMMITTED", h.receive("valid-wg")); assertEquals(1, h.state().getAsJsonArray("outbox").size()); assertEquals(1, h.app.applies);
        }
    }
    @Test public void networkSendReleasesOwnerAndPreservesConcurrentNewAcks() throws Exception {
        try (Harness h = new Harness()) {
            h.receive("valid-wg"); ExecutorService worker = Executors.newSingleThreadExecutor();
            boolean[] once = {false};
            try {
                assertFalse(h.core.flush(raw -> {
                    if (!once[0]) { once[0] = true;
                        assertEquals("COMMITTED", worker.submit(() -> h.receive("valid-next")).get(3, TimeUnit.SECONDS));
                    } return true;
                }));
                assertEquals(3, h.state().getAsJsonArray("outbox").size());
                for (JsonElement e : h.state().getAsJsonArray("outbox")) assertEquals(2, h.journal.receipt(e).get("sequence").getAsLong());
            } finally { worker.shutdownNow(); }
        }
    }
    @Test public void saturatedOutboxRefusesBeforeApply() throws Exception {
        try (Harness h = new Harness()) {
            JsonObject r = h.state(); r.addProperty("last_now", 1000);
            for (int i = 0; i < 59; i++) r.getAsJsonArray("outbox").add(Base64.getEncoder().encodeToString(h.identity.acknowledgement(String.format(Locale.ROOT,"%064x",i),null,0,"REJECTED","SIGNATURE",1000)));
            h.journal.save(r); assertThrows(IOException.class, () -> h.receive("valid-wg")); assertEquals(0, h.app.applies);
            assertEquals(0, h.app.snapshots); assertEquals(0, h.state().get("floor").getAsLong());
        }
    }
    @Test public void corruptOrMissingStateNeverReinitializes() throws Exception {
        try (Harness h = new Harness()) {
            assertThrows(IOException.class, h.journal::initialize);
            JsonObject good = h.state();
            List<JsonObject> bad = new ArrayList<>();
            JsonObject r = good.deepCopy(); r.addProperty("floor", true); bad.add(r);
            r = good.deepCopy(); r.addProperty("schema", true); bad.add(r);
            r = good.deepCopy(); r.addProperty("device", "00000000000000000000000000000000"); bad.add(r);
            r = good.deepCopy(); r.addProperty("phase", "APPLYING"); bad.add(r);
            for (JsonObject invalid : bad) { h.store.raw = ControlJournal.encode(invalid); assertThrows(Exception.class, h.core::recover); }
            h.store.raw = "{\"schema\":1,\"schema\":1}".getBytes(); assertThrows(Exception.class, h.core::recover);
            h.store.raw = null; assertThrows(IOException.class, h.core::recover); assertEquals(0,h.app.applies);
        }
    }
    @Test public void acknowledgementsMatchPythonCanonicalBytes() throws Exception {
        try (Harness h = new Harness()) {
            JsonObject m = ControlJson.parse(resource("manifest.json")).getAsJsonObject(); int count = 0;
            for (JsonElement item : m.getAsJsonArray("acknowledgements")) {
                JsonObject v = item.getAsJsonObject(); if (!v.getAsJsonObject("expected").get("category").getAsString().equals("ACCEPT")) continue;
                byte[] reference = resource(v.get("input").getAsString()); JsonObject body = ControlProtocol.verifyAck(reference);
                byte[] actual = h.identity.acknowledgement(body.get("envelope_hash").getAsString(),body.get("config_id").isJsonNull()?null:body.get("config_id").getAsString(),body.get("sequence").getAsLong(),body.get("status").getAsString(),body.get("error").getAsString(),body.get("timestamp").getAsLong());
                // The size-limit fixture appends unsigned JSON whitespace. Canonical body/signature remain identical.
                assertArrayEquals(new String(reference, java.nio.charset.StandardCharsets.UTF_8).stripTrailing().getBytes(java.nio.charset.StandardCharsets.UTF_8), actual); count++;
            } assertTrue(count > 0);
        }
    }
    @Test public void immutablePythonTransactionTranscripts() throws Exception {
        JsonObject manifest = ControlJson.parse(resource("manifest.json")).getAsJsonObject(); int steps = 0;
        for (JsonElement transcript : manifest.getAsJsonArray("transcripts")) {
            try (Harness h = new Harness()) {
                h.app.runtime.addProperty("candidate", "baseline");
                for (JsonElement element : transcript.getAsJsonObject().getAsJsonArray("steps")) {
                    JsonObject step = element.getAsJsonObject(), expected = step.getAsJsonObject("expected");
                    if (step.has("health")) h.app.healthy = step.get("health").getAsBoolean();
                    JsonElement result;
                    switch (step.get("operation").getAsString()) {
                        case "receive": result = new JsonPrimitive(h.receive(step.get("input").getAsString())); break;
                        case "crash":
                            assertEquals("APPLIED_PENDING", step.get("at_phase").getAsString());
                            h.store.failAt = h.store.writes + 3; h.store.after = true;
                            assertThrows(Death.class, () -> h.receive(step.get("input").getAsString()));
                            h.store.failAt = -1; result = new JsonPrimitive("CRASH"); break;
                        case "restart-recover": h.restart(); result = new JsonPrimitive(h.core.recover()); break;
                        case "flush":
                            result = new JsonPrimitive(h.core.flush(raw -> step.get("available").getAsBoolean()));
                            assertEquals(step.get("outbox_empty").getAsBoolean(), h.state().getAsJsonArray("outbox").isEmpty()); break;
                        default: throw new AssertionError("Unknown transcript operation");
                    }
                    JsonObject state = h.state();
                    assertEquals(expected.get("result"), result);
                    assertEquals(expected.get("floor").getAsLong(), state.get("floor").getAsLong());
                    assertEquals(expected.get("phase"), state.get("phase"));
                    assertEquals(expected.get("applies").getAsInt(), h.app.applies);
                    assertEquals(expected.get("rollbacks").getAsInt(), h.app.rollbacks);
                    assertEquals(expected.get("active"), h.app.runtime.get("candidate"));
                    assertEquals(expected.get("committed_sha256"), state.get("committed").isJsonNull() ? JsonNull.INSTANCE : state.getAsJsonObject("committed").get("digest"));
                    if (step.has("error")) assertEquals(step.get("error"), lastAck(h).get("error"));
                    steps++;
                }
            }
        }
        assertEquals(16, steps);
    }
    @Test public void storedEnvelopesAndReceiptsAreReverified() throws Exception {
        try (Harness h = new Harness()) {
            h.receive("valid-wg"); JsonObject original = h.state(); List<JsonObject> bad = new ArrayList<>();
            JsonObject r = original.deepCopy(); r.addProperty("floor", 0); bad.add(r);
            r = original.deepCopy(); r.getAsJsonObject("committed").addProperty("digest", String.format("%064d",0)); bad.add(r);
            r = original.deepCopy(); r.getAsJsonObject("committed").addProperty("at", 4600); bad.add(r);
            r = original.deepCopy(); r.getAsJsonObject("committed").addProperty("applied_at", true); bad.add(r);
            r = original.deepCopy(); r.getAsJsonArray("outbox").add(r.getAsJsonArray("outbox").get(0)); bad.add(r);
            r = original.deepCopy(); r.addProperty("result", Base64.getEncoder().encodeToString("{}".getBytes())); bad.add(r);
            try (ControlIdentity other = ControlIdentity.generate()) {
                r = original.deepCopy(); r.getAsJsonArray("outbox").set(0, new JsonPrimitive(Base64.getEncoder().encodeToString(other.acknowledgement(String.format("%064d",0),null,0,"REJECTED","SIGNATURE",1000)))); bad.add(r);
            }
            for (JsonObject invalid : bad) {
                h.store.raw = ControlJournal.encode(invalid); assertThrows(Exception.class, h.core::recover);
                assertEquals(0, h.app.rollbacks); assertEquals(1, h.app.applies);
            }
        }
    }
    @Test public void journalEncryptionBoundsAndIdentityDomainSeparation() throws Exception {
        KeyGenerator g = KeyGenerator.getInstance("AES"); g.init(256); var key = g.generateKey();
        for (int size : new int[]{1,125,ControlJournal.LIMIT}) {
            byte[] plain = new byte[size]; new Random(42).nextBytes(plain);
            byte[] sealed = ControlJournalEnvelope.seal(key, plain); assertArrayEquals(plain,ControlJournalEnvelope.open(key,sealed));
            sealed[sealed.length-1] ^= 1; assertThrows(Exception.class, () -> ControlJournalEnvelope.open(key,sealed));
        }
        assertThrows(Exception.class, () -> ControlJournalEnvelope.seal(key,new byte[ControlJournal.LIMIT+1]));
        assertThrows(Exception.class, () -> ControlJournalEnvelope.open(key,new byte[ControlJournal.LIMIT+30]));
        assertThrows(Exception.class, () -> ControlJournalEnvelope.open(key,ControlIdentityEnvelope.seal(key,new byte[96])));
    }
}
