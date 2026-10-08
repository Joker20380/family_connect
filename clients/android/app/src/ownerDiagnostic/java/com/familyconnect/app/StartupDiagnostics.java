package com.familyconnect.app;

import android.content.Context;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

final class StartupDiagnostics {
    private static long active;
    private static StartupResult latest;
    private static String collection = "ABSENT";

    private static AtomicFile file(Context context) { return new AtomicFile(new File(context.getNoBackupFilesDir(), "diag-owner-startup.json")); }

    private static void write(Context context, String value) throws Exception {
        byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 4096) throw new IllegalArgumentException("Startup result bound");
        AtomicFile target = file(context);
        FileOutputStream output = target.startWrite();
        try { output.write(bytes); target.finishWrite(output); }
        catch (Exception failure) { target.failWrite(output); throw failure; }
    }

    static synchronized void begin(Context context, long handle) {
        if (handle <= active) return;
        active = handle;
        latest = null;
        collection = "PENDING";
        try { write(context, new JSONObject().put("collection", collection).put("attempt", handle).toString()); }
        catch (Exception failure) { collection = "COLLECTION_ERROR"; }
    }

    static synchronized void capture(Context context, long handle, JSONObject stats) {
        if (handle != active || handle <= 0) return;
        try {
            StartupResult next = new StartupResult(stats.getJSONObject("owner_startup").toString());
            if (next.attempt != active) { collection = "ATTEMPT_MISMATCH"; return; }
            if (latest != null && latest.complete && "AVAILABLE".equals(collection)) return;
            if (latest != null && latest.complete) next = latest;
            latest = next;
            write(context, next.json);
            collection = "AVAILABLE";
        } catch (Exception failure) { collection = "COLLECTION_ERROR"; }
    }

    static void stopped(Context context, long handle) {
        try { capture(context, handle, new JSONObject(NativeRestricted.stats(handle))); }
        catch (Exception | LinkageError failure) { synchronized (StartupDiagnostics.class) { if (handle == active) collection = "COLLECTION_ERROR"; } }
    }

    static synchronized ConnectivityOrchestrator.Rejected rejected(long handle, ConnectivityOrchestrator.Failure category) {
        ConnectivityOrchestrator.Rejected result = new ConnectivityOrchestrator.Rejected(category);
        Throwable cause = latest == null || handle != active ? null : latest.failure();
        if (cause != null) result.initCause(cause);
        return result;
    }

    static synchronized String read(Context context) {
        try {
            if (latest != null) return new JSONObject().put("collection", collection).put("result", new JSONObject(latest.json)).toString();
            if (active > 0 && "COLLECTION_ERROR".equals(collection)) return "{\"collection\":\"COLLECTION_ERROR\"}";
            File path = file(context).getBaseFile();
            if (path.length() > 4096) return "{\"collection\":\"UNSUPPORTED_FORMAT\"}";
            JSONObject stored = new JSONObject(new String(file(context).readFully(), StandardCharsets.UTF_8));
            if ("PENDING".equals(stored.optString("collection"))) return "{\"collection\":\"PENDING\"}";
            StartupResult result = new StartupResult(stored.toString());
            if (active > 0 && result.attempt != active) return "{\"collection\":\"ATTEMPT_MISMATCH\"}";
            return new JSONObject().put("collection", "AVAILABLE").put("result", new JSONObject(result.json)).toString();
        } catch (FileNotFoundException missing) { return file(context).getBaseFile().exists() ? "{\"collection\":\"COLLECTION_ERROR\"}" : "{\"collection\":\"ABSENT\"}"; }
        catch (org.json.JSONException | IllegalArgumentException invalid) { return "{\"collection\":\"UNSUPPORTED_FORMAT\"}"; }
        catch (Exception failure) { return "{\"collection\":\"COLLECTION_ERROR\"}"; }
    }
}
