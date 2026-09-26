package com.familyconnect.app;

import android.content.Context;
import android.os.Looper;
import com.chaquo.python.PyObject;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.util.Arrays;

/** One chat owner per process. Call from a worker, never the UI thread.
 * Delivery is opt-in after authenticated bootstrap; close joins its worker.
 */
final class ChatLocalAndroid implements AutoCloseable {
    private static final Object LOCK = new Object();
    private static ChatLocalAndroid active;
    private PyObject session;
    private ChatStoreCipher cipher;
    private Context context;

    static final class ChatException extends Exception {
        final String code;
        ChatException(String code) { super(code); this.code = code; }
    }

    private ChatLocalAndroid() {}

    static boolean hasState(Context context) throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            try {
                return Files.exists(new File(context.getNoBackupFilesDir(), "chat-store").toPath(),
                    LinkOption.NOFOLLOW_LINKS) || new ChatKeyVault(context).hasState();
            } catch (Exception failure) { throw new ChatException("store_unavailable"); }
        }
    }

    static ChatLocalAndroid open(Context context, boolean create) throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            if (active != null) throw new ChatException("busy");
            ChatLocalAndroid owner = new ChatLocalAndroid();
            byte[] key = null;
            try {
                Context app = context.getApplicationContext();
                owner.context = app;
                File directory = new File(app.getNoBackupFilesDir(), "chat-store");
                if (create && Files.exists(directory.toPath(), LinkOption.NOFOLLOW_LINKS))
                    throw new ChatException("store_unavailable");
                var python = PythonRuntimeAndroid.get(app);
                var module = python.getModule("fc_chat_store");
                ChatKeyVault vault = new ChatKeyVault(app);
                key = create ? vault.create() : vault.load();
                owner.cipher = new ChatStoreCipher(key);
                Arrays.fill(key, (byte) 0);
                owner.session = module.callAttr("Session", directory.getAbsolutePath(),
                    new File(app.getNoBackupFilesDir(), "rns-control").getAbsolutePath(), owner.cipher, create);
                active = owner;
                return owner;
            } catch (Exception failure) {
                if (owner.cipher != null) owner.cipher.close();
                // Never retry enrollment, rotate a key, erase files or expose a traceback.
                throw new ChatException("store_unavailable");
            } finally {
                if (key != null) Arrays.fill(key, (byte) 0);
            }
        }
    }

    JsonElement call(String operation, JsonObject arguments) throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            if (session == null) throw new ChatException("closed");
            try {
                String reply = session.callAttr("invoke", operation, arguments.toString()).toString();
                JsonObject result = JsonParser.parseString(reply).getAsJsonObject();
                if (!result.get("ok").getAsBoolean()) throw new ChatException(result.get("error").getAsString());
                return result.get("value");
            } catch (ChatException failure) {
                throw failure;
            } catch (Exception failure) {
                throw new ChatException("store_unavailable");
            }
        }
    }

    // Platform enrollment must supply a trusted mailbox anchor, never contact-card JSON.
    JsonObject enrollmentProof(String device, String challenge) throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            if (session == null) throw new ChatException("closed");
            try {
                return JsonParser.parseString(session.callAttr("enrollment_proof", device, challenge).toString()).getAsJsonObject();
            } catch (Exception failure) { throw new ChatException("enrollment_unavailable"); }
        }
    }

    void configureDelivery(String host, int port, String publicHex) throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            if (session == null) throw new ChatException("closed");
            try {
                session.callAttr("configure_delivery", host, port, publicHex,
                    new ChatNetworkAndroid(context));
            } catch (Exception failure) { throw new ChatException("delivery_unavailable"); }
        }
    }

    void deliveryUpdate(boolean online, boolean foreground) throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            if (session == null) throw new ChatException("closed");
            try { session.callAttr("delivery_update", online, foreground); }
            catch (Exception failure) { throw new ChatException("delivery_unavailable"); }
        }
    }

    @Override public void close() throws ChatException {
        requireWorker();
        synchronized (LOCK) {
            if (session == null) return;
            try {
                session.callAttr("close");
            } catch (Exception failure) {
                // Retain ownership/cipher if the Store could not close safely.
                throw new ChatException("close_failed");
            }
            session.close(); session = null;
            cipher.close(); cipher = null;
            context = null;
            active = null;
        }
    }

    private static void requireWorker() throws ChatException {
        if (Looper.myLooper() == Looper.getMainLooper()) throw new ChatException("worker_required");
    }
}
