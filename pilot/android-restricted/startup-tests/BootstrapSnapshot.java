package com.familyconnect.bootstraplocalize;

import android.app.Instrumentation;
import android.content.Context;
import android.content.pm.PackageInfo;
import android.os.Bundle;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.JSONArray;
import org.json.JSONObject;

public final class BootstrapSnapshot extends Instrumentation {
    private static final String PACKAGE = "com.familyconnect.app.friends";
    private static final String PIN = "67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a";
    private static final int LIMIT = 2 * 1024 * 1024;
    private Bundle options;

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        options=arguments;
        start();
    }

    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte value : bytes) result.append(String.format("%02x", value & 255));
        return result.toString();
    }

    private static String fileHash(File file) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(FileInputStream stream=new FileInputStream(file)) {
            byte[] bytes=new byte[65536];int count;
            while((count=stream.read(bytes))!=-1)digest.update(bytes,0,count);
        }
        return hex(digest.digest());
    }

    private void startup(Context target) throws Exception {
        Class<?> diagnostics=Class.forName("com.familyconnect.app.StartupDiagnostics",true,target.getClassLoader());
        java.lang.reflect.Method method=diagnostics.getDeclaredMethod("read",Context.class);
        method.setAccessible(true);
        JSONObject value=new JSONObject((String)method.invoke(null,target));
        value.put("event","STARTUP_RESULT");
        if("AVAILABLE".equals(value.optString("collection")) && value.getJSONObject("result").getLong("attempt")!=Long.parseLong(options.getString("expected_attempt")))throw new IllegalStateException("Startup attempt identity");
        report(value);
        if(!"AVAILABLE".equals(value.optString("collection")))throw new IllegalStateException("Startup collection unavailable");
    }

    private void report(JSONObject value) {
        Bundle status = new Bundle();
        status.putString("bootstrap_evidence", value.toString());
        sendStatus(2, status);
    }

    private static JSONObject safe(JSONObject source) throws Exception {
        JSONObject result = new JSONObject();
        if (source == null) return result;
        for (String key : new String[]{"state", "timestamp", "elapsed_ms", "timestamp_ms", "sequence", "duration_ms", "observed_at_ms", "terminal_at_ms", "terminal_observed_at_ms", "native_state", "protect_ok", "protect_denied", "underlay_dns", "goroutines", "go_heap", "pss_kib", "cpu_ms", "authorization_denied", "failed", "dns", "tcp", "active", "tcp_active", "tcp_peak", "peak", "retransmissions", "recovery_timeouts", "vpn_capture_open", "version_code"}) {
            Object value = source.opt(key);
            if (value instanceof Number || value instanceof Boolean) result.put(key, value);
        }
        for (String key : new String[]{"state", "stage", "reason", "event", "component", "reason_code", "state_from", "state_to", "transport_class", "network_class", "restricted_readiness", "bootstrap_directory", "terminal_reason", "reliable_terminal", "signaling_failure", "ice_failure", "publisher_state", "subscriber_state", "owner_status", "owner_health", "java_failure", "correlation_status"}) {
            Object value = source.opt(key);
            if (value instanceof String && ((String)value).matches("[A-Za-z0-9_]{1,80}")) result.put(key, value);
        }
        JSONArray events = source.optJSONArray("events");
        if (source.has("events")) result.put("events_collection", events == null ? "UNSUPPORTED_FORMAT" : "COMPLETE");
        if (events != null) {
            JSONArray filtered = new JSONArray();
            int unsupported = 0;
            for (int index = 0; index < Math.min(128, events.length()); index++) {
                Object event = events.opt(index);
                if (event instanceof String && ((String)event).matches("[a-z0-9_]{1,80}")) filtered.put(event);
                else if (event instanceof JSONObject) filtered.put(safe((JSONObject)event));
                else unsupported++;
            }
            result.put("events", filtered);
            result.put("events_unsupported", unsupported).put("events_projection_dropped", Math.max(0, events.length()-128));
            result.put("events_history", "EVICTION_OR_RESET_UNKNOWN");
            if (unsupported > 0) result.put("events_collection", "PARTIAL_UNSUPPORTED");
            else if (events.length()>128) result.put("events_collection", "BOUNDED");
        }
        for (String key : new String[]{"packet", "diagnostic", "restricted_session", "lifecycle", "first_failure", "terminal", "counters"}) {
            if (source.optJSONObject(key) != null) result.put(key, safe(source.getJSONObject(key)));
        }
        JSONArray trace = source.optJSONArray("trace");
        if (trace != null) {
            JSONArray filtered = new JSONArray();
            for (int index = 0; index < Math.min(128, trace.length()); index++) {
                if (trace.optJSONObject(index) != null) filtered.put(safe(trace.getJSONObject(index)));
            }
            result.put("trace", filtered);
        }
        JSONArray history = source.optJSONArray("restricted_history");
        if (history != null) {
            JSONArray filtered = new JSONArray();
            for (int index = 0; index < Math.min(4, history.length()); index++) {
                if (history.optJSONObject(index) != null) filtered.put(safe(history.getJSONObject(index)));
            }
            result.put("restricted_history", filtered);
        }
        return result;
    }

    private static JSONObject project(String raw) throws Exception {
        try {
            JSONObject source = new JSONObject(raw);
            JSONObject result = safe(source);
            result.put("collection", "PARSED");
            if (!source.has("events")) result.put("events_collection", "ABSENT_FIELD");
            return result;
        } catch (org.json.JSONException invalid) {
            return new JSONObject().put("collection", "COLLECTION_ERROR").put("reason", "INVALID_JSON");
        }
    }

    private void read(File file, String label, boolean lines) throws Exception {
        JSONObject metadata = new JSONObject().put("file", label).put("exists", file.isFile()).put("bytes", file.length()).put("modified_ms", file.lastModified());
        report(metadata);
        if (!file.isFile()) { report(new JSONObject().put("file",label).put("collection","FILE_ABSENT")); return; }
        if (file.length() > LIMIT) throw new IllegalStateException("Evidence bound");
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (FileInputStream input = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        metadata.put("sha256", hex(digest.digest()));
        report(metadata);
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8))) {
            String line;
            int number = 0;
            while ((line = reader.readLine()) != null) {
                if (++number > 4096) throw new IllegalStateException("Evidence count bound");
                JSONObject filtered = project(line);
                filtered.put("file", label).put("record", number);
                report(filtered);
                if ("COLLECTION_ERROR".equals(filtered.optString("collection"))) throw new IllegalStateException("Evidence parse failed");
                if (!lines) break;
            }
        }
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            Context target = getTargetContext();
            PackageInfo info = target.getPackageManager().getPackageInfo(PACKAGE, android.content.pm.PackageManager.GET_SIGNING_CERTIFICATES);
            if (!target.getPackageName().equals(PACKAGE) || info.getLongVersionCode() != 71) throw new IllegalStateException("Package identity");
            if(options==null || !"71".equals(options.getString("expected_version")) || !fileHash(new File(target.getApplicationInfo().sourceDir)).equals(options.getString("expected_apk_sha256")))throw new IllegalStateException("Artifact identity");
            android.content.pm.Signature[] signers = info.signingInfo.getApkContentsSigners();
            if (signers.length != 1 || !PIN.equals(hex(MessageDigest.getInstance("SHA-256").digest(signers[0].toByteArray())))) throw new IllegalStateException("Signer identity");
            report(new JSONObject().put("event", "READ_ONLY_ENTER").put("wall_ms", System.currentTimeMillis()).put("elapsed_ms", android.os.SystemClock.elapsedRealtime()));
            startup(target);
            read(new File(target.getFilesDir(), "restricted-evidence.jsonl"), "restricted-evidence", true);
            read(new File(target.getNoBackupFilesDir(), "diag-ring.json"), "diag-ring", false);
            read(new File(target.getNoBackupFilesDir(), "diag-incident.json"), "diag-incident", false);
            result.putString("result", "PASS_READ_ONLY");
            finish(-1, result);
        } catch (Exception failure) {
            result.putString("result", "COLLECTION_ERROR");
            result.putString("failure_class", failure.getClass().getSimpleName());
            finish(1, result);
        }
    }
}
