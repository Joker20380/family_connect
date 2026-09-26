package com.familyconnect.app;

import android.content.Context;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.google.gson.JsonObject;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.KeyStore;
import java.util.Arrays;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class ChatLocalRuntimeTest {
    static Context context() {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        if (!context.getPackageName().equals("com.familyconnect.chatchecks"))
            throw new AssertionError("Only the isolated chat acceptance app is allowed");
        return context;
    }
    static File root() { return context().getNoBackupFilesDir(); }
    static void reset() throws Exception {
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null);
        keys.deleteEntry("family-connect-chat-store-v1");
        for (String name : new String[]{"chat-store", "chat-store-key.enc", "chat-store-key.enc.bak", "chat-store-key.enc.new", "chat-receipt.json"})
            remove(new File(root(), name));
    }
    private static void remove(File path) throws Exception {
        File[] children = path.listFiles();
        if (children != null) for (File child : children) remove(child);
        Files.deleteIfExists(path.toPath());
    }
    static JsonObject args(String... pairs) {
        JsonObject result = new JsonObject();
        for (int i = 0; i < pairs.length; i += 2) result.addProperty(pairs[i], pairs[i + 1]);
        return result;
    }
    static JsonObject peer(ChatLocalAndroid chat) throws Exception {
        char[] chars = new char[128]; Arrays.fill(chars, '1');
        return chat.call("preview_contact", args("public", new String(chars))).getAsJsonObject();
    }
    static void trust(ChatLocalAndroid chat, JsonObject peer) throws Exception {
        chat.call("trust_contact", args("public", peer.get("public").getAsString(),
            "fingerprint", peer.get("fingerprint").getAsString()));
    }
    static JsonObject history(ChatLocalAndroid chat, JsonObject peer) throws Exception {
        JsonObject args = args("address", peer.get("address").getAsString());
        args.addProperty("offset", 0); args.addProperty("limit", 50);
        return chat.call("history", args).getAsJsonObject();
    }
    static void refused(boolean create) throws Exception {
        try (ChatLocalAndroid unexpected = ChatLocalAndroid.open(context(), create)) { fail("Account unexpectedly opened"); }
        catch (ChatLocalAndroid.ChatException expected) { assertEquals("store_unavailable", expected.code); }
    }

    @Test public void deliveryOwnershipClosesAndReopensWithoutNetwork() throws Exception {
        reset();
        for (int attempt = 0; attempt < 2; attempt++) {
            try (ChatLocalAndroid chat = ChatLocalAndroid.open(context(), attempt == 0)) {
                String anchor = peer(chat).get("public").getAsString();
                chat.configureDelivery("127.0.0.1", 4243, anchor);
                chat.deliveryUpdate(false, true);
                JsonObject state = chat.call("delivery_state", args()).getAsJsonObject();
                assertTrue(state.get("attached").getAsBoolean());
                assertEquals(0, state.get("attempts").getAsInt());
                assertFalse(state.get("running").getAsBoolean());
                chat.deliveryUpdate(false, false);
            }
        }
        reset();
    }

    @Test public void keystoreBridgeResumeAndCorruption() throws Exception {
        reset();
        JsonObject profile, peer; String id;
        try (ChatLocalAndroid chat = ChatLocalAndroid.open(context(), true)) {
            var python = PythonRuntimeAndroid.get(context());
            assertEquals("1.5.1", python.getModule("RNS").get("__version__").toString());
            assertEquals("1.1.1", python.getModule("LXMF").get("__version__").toString());
            assertEquals("internal", python.getModule("RNS.Cryptography.Provider").callAttr("backend").toString());
            profile = chat.call("profile", args()).getAsJsonObject();
            peer = peer(chat); trust(chat, peer);
            id = chat.call("queue", args("address", peer.get("address").getAsString(), "text", "История 🙂 :)")).getAsString();
            assertEquals(1, history(chat, peer).get("total").getAsInt());
            try { ChatLocalAndroid.open(context(), false); fail("Second owner admitted"); }
            catch (ChatLocalAndroid.ChatException expected) { assertEquals("busy", expected.code); }
        }
        try (ChatLocalAndroid chat = ChatLocalAndroid.open(context(), false)) {
            assertEquals(profile, chat.call("profile", args()));
            var message = history(chat, peer).getAsJsonArray("messages").get(0).getAsJsonObject();
            assertEquals(id, message.get("id").getAsString());
            assertEquals("История 🙂 :)", message.get("text").getAsString());
            assertEquals("queued", message.get("status").getAsString());
            assertFalse(message.has("packed")); assertFalse(message.has("attempt"));
        }
        byte[] database = Files.readAllBytes(new File(root(), "chat-store/history.sqlite").toPath());
        assertFalse(new String(database, StandardCharsets.UTF_8).contains("История"));
        File envelope = new File(root(), "chat-store-key.enc");
        byte[] raw = Files.readAllBytes(envelope.toPath()); raw[raw.length - 1] ^= 1;
        Files.write(envelope.toPath(), raw);
        refused(false); refused(true);
        assertArrayEquals(database, Files.readAllBytes(new File(root(), "chat-store/history.sqlite").toPath()));
        reset();
    }

    @Test public void orphanAndMissingDatabaseNeverRegenerate() throws Exception {
        reset();
        assertFalse(ChatLocalAndroid.hasState(context()));
        try (ChatLocalAndroid chat = ChatLocalAndroid.open(context(), true)) { chat.call("profile", args()); }
        Files.delete(new File(root(), "chat-store/history.sqlite").toPath());
        assertTrue(ChatLocalAndroid.hasState(context()));
        refused(false); refused(true);
        assertFalse(new File(root(), "chat-store/history.sqlite").exists());
        reset();
        byte[] key = new ChatKeyVault(context()).create(); Arrays.fill(key, (byte) 0);
        assertTrue(ChatLocalAndroid.hasState(context()));
        refused(false); refused(true);
        assertFalse(new File(root(), "chat-store").exists());
        reset();
    }

    @Test public void missingWrappingKeyDoesNotReplaceHistory() throws Exception {
        reset();
        try (ChatLocalAndroid chat = ChatLocalAndroid.open(context(), true)) { chat.call("profile", args()); }
        byte[] before = Files.readAllBytes(new File(root(), "chat-store/history.sqlite").toPath());
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null);
        keys.deleteEntry("family-connect-chat-store-v1");
        assertTrue(ChatLocalAndroid.hasState(context()));
        refused(false); refused(true);
        assertFalse(keys.containsAlias("family-connect-chat-store-v1"));
        assertArrayEquals(before, Files.readAllBytes(new File(root(), "chat-store/history.sqlite").toPath()));
        reset();
    }
}
