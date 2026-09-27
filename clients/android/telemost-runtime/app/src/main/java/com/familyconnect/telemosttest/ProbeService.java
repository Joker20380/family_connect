package com.familyconnect.telemosttest;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.BatteryManager;
import android.os.Binder;
import android.os.Debug;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.SystemClock;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.HashSet;
import java.util.Arrays;

public final class ProbeService extends Service {
    private static final Set<String> EVENTS = new HashSet<>(Arrays.asList("start", "connected", "family_auth", "probe_result", "probe_failed", "suite_complete", "summary", "resources", "perf_warmup", "perf_sample", "perf_blocks", "perf_result", "reliability_final"));
    final class LocalBinder extends Binder { ProbeService service() { return ProbeService.this; } }
    private final LocalBinder binder = new LocalBinder();
    private final NativeRun run = new NativeRun();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final StringBuilder tail = new StringBuilder();
    private long started;
    private int records;
    private int generation;
    private boolean destroying;
    private final BroadcastReceiver screen = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            lifecycle(Intent.ACTION_SCREEN_OFF.equals(intent.getAction()) ? "screen_off" : "screen_on");
        }
    };
    private final Runnable deadline = this::disconnect;
    private final Runnable sample = new Runnable() {
        @Override public void run() {
            if (!run.isActive()) return;
            Debug.MemoryInfo memory = new Debug.MemoryInfo();
            Debug.getMemoryInfo(memory);
            BatteryManager battery = getSystemService(BatteryManager.class);
            record(event("android_resources", "elapsed_ms", SystemClock.elapsedRealtime() - started,
                "java_used_bytes", Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory(),
                "app_pss_kib", memory.getTotalPss(), "app_cpu_ms", android.os.Process.getElapsedCpuTime(),
                "battery_percent", battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY),
                "network", networkType()));
            if (vpnPresent()) {
                record(event("android_failure", "reason", "VPN_PRESENT_UNPROTECTED"));
                disconnect();
                return;
            }
            handler.postDelayed(this, 10000);
        }
    };

    @Override public IBinder onBind(Intent intent) { return binder; }
    @Override public void onCreate() {
        super.onCreate();
        IntentFilter filter = new IntentFilter();
        filter.addAction(Intent.ACTION_SCREEN_OFF);
        filter.addAction(Intent.ACTION_SCREEN_ON);
        if (android.os.Build.VERSION.SDK_INT >= 33) registerReceiver(screen, filter, RECEIVER_NOT_EXPORTED);
        else registerReceiver(screen, filter);
    }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && "disconnect".equals(intent.getAction())) disconnect();
        return START_NOT_STICKY;
    }

    synchronized String snapshot() { return tail.toString(); }
    boolean active() { return run.isActive(); }
    void lifecycle(String state) { if (run.isActive()) record(event("android_lifecycle", "state", state)); }

    void startProbe(String room) {
        if (destroying || run.isActive()) return;
        if (room == null || room.length() > 2048 || !room.startsWith("https://")) {
            record(event("android_failure", "reason", "ROOM_INPUT_INVALID"));
            return;
        }
        if (vpnPresent()) {
            record(event("android_failure", "reason", "VPN_PRESENT_UNPROTECTED"));
            return;
        }
        File executable = new File(getApplicationInfo().nativeLibraryDir, "libfc_telemost.so");
        if (!executable.canExecute()) {
            record(event("android_failure", "reason", "NATIVE_PACKAGING_NOT_EXECUTABLE"));
            return;
        }
        synchronized (this) {
            tail.setLength(0);
            records = 0;
            try (FileOutputStream output = openFileOutput("evidence.jsonl", MODE_PRIVATE)) {
                output.flush();
            } catch (Exception ignored) { return; }
        }
        started = SystemClock.elapsedRealtime();
        int currentGeneration = ++generation;
        startForegroundService(new Intent(this, ProbeService.class));
        NotificationManager notifications = getSystemService(NotificationManager.class);
        notifications.createNotificationChannel(new NotificationChannel("probe", "Synthetic carrier test", NotificationManager.IMPORTANCE_LOW));
        PendingIntent stop = PendingIntent.getService(this, 1, new Intent(this, ProbeService.class).setAction("disconnect"), PendingIntent.FLAG_IMMUTABLE);
        startForeground(1, new Notification.Builder(this, "probe")
            .setContentTitle("Telemost isolated VP8 test")
            .setContentText("No VPN. Family auth only with test credentials. Tap to disconnect.")
            .setSmallIcon(android.R.drawable.stat_notify_sync).setContentIntent(stop).setOngoing(true).build());
        record(event("android_start", "model", android.os.Build.MODEL, "android", android.os.Build.VERSION.RELEASE,
            "abi", android.os.Build.SUPPORTED_ABIS[0], "network", networkType(), "protected_sockets", false));
        run.start(() -> {
            ProcessBuilder builder = new ProcessBuilder(executable.getAbsolutePath(), "--role", "probe", "--mode", "vp8",
                "--duration", "25m", "--sustained", "30s", "--extended", "--metrics-interval", "10s");
            File performance = new File(getFilesDir(), "performance.input");
            if (performance.isFile()) {
                builder.command().addAll(Arrays.asList("--performance-config", performance.getAbsolutePath()));
            }
            File family = new File(getFilesDir(), "family.input");
            if (family.exists()) {
                builder.command().add("--family-config");
                builder.command().add(family.getAbsolutePath());
            }
            builder.environment().put("FC_TELEMOST_ROOM", room);
            builder.environment().put("SSL_CERT_DIR", "/system/etc/security/cacerts:/apex/com.android.conscrypt/cacerts");
            builder.redirectError(new File("/dev/null"));
            try { return builder.start(); }
            finally { builder.environment().remove("FC_TELEMOST_ROOM"); }
        }, new NativeRun.Observer() {
            @Override public void line(String line) {
                try {
                    JSONObject data = new JSONObject(line);
                    if ("start".equals(data.optString("event"))) {
                        int nativePid = data.getInt("pid");
                        if (nativePid <= 1 || data.getInt("parent_pid") != android.os.Process.myPid()) {
                            throw new IllegalStateException("native process ownership mismatch");
                        }
                        run.setStopSignal(() -> android.os.Process.sendSignal(nativePid, 15));
                    }
                    if (!EVENTS.contains(data.optString("event")) || line.contains("://")) {
                        record(event("android_failure", "reason", "OUTPUT_REJECTED"));
                        run.cancel();
                        return;
                    }
                    record(data);
                } catch (Exception ignored) {
                    record(event("android_failure", "reason", "OUTPUT_INVALID"));
                    run.cancel();
                }
            }
            @Override public void finished(int code, boolean cancelled) {
                record(event("android_exit", "code", code, "cancelled", cancelled,
                    "elapsed_ms", SystemClock.elapsedRealtime() - started));
                handler.post(() -> {
                    if (currentGeneration != generation) return;
                    handler.removeCallbacks(sample);
                    handler.removeCallbacks(deadline);
                    stopForeground(STOP_FOREGROUND_REMOVE);
                    stopSelf();
                });
            }
        });
        handler.post(sample);
        handler.postDelayed(deadline, 25 * 60 * 1000L);
    }

    void disconnect() {
        handler.removeCallbacks(deadline);
        handler.removeCallbacks(sample);
        run.cancel();
        if (!run.isActive()) {
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
        }
    }

    @Override public void onTaskRemoved(Intent rootIntent) { disconnect(); }
    @Override public void onDestroy() {
        destroying = true;
        unregisterReceiver(screen);
        disconnect();
        super.onDestroy();
    }

    private boolean vpnPresent() {
        ConnectivityManager manager = getSystemService(ConnectivityManager.class);
        for (Network network : manager.getAllNetworks()) {
            NetworkCapabilities capabilities = manager.getNetworkCapabilities(network);
            if (capabilities != null && capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) return true;
        }
        return false;
    }

    private String networkType() {
        ConnectivityManager manager = getSystemService(ConnectivityManager.class);
        NetworkCapabilities capabilities = manager.getNetworkCapabilities(manager.getActiveNetwork());
        if (capabilities == null) return "none";
        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) return "wifi";
        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) return "cellular";
        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) return "vpn";
        return "other";
    }

    private static JSONObject event(String name, Object... fields) {
        JSONObject data = new JSONObject();
        try {
            data.put("event", name);
            data.put("utc_ms", System.currentTimeMillis());
            for (int index = 0; index < fields.length; index += 2) data.put((String) fields[index], fields[index + 1]);
        } catch (Exception ignored) { throw new IllegalArgumentException("invalid metrics"); }
        return data;
    }

    private synchronized void record(JSONObject data) {
        String line = data.toString() + "\n";
        if (++records > 1024 || new File(getFilesDir(), "evidence.jsonl").length() + line.length() > 2 * 1024 * 1024) {
            handler.post(this::disconnect);
            return;
        }
        try (FileOutputStream output = openFileOutput("evidence.jsonl", MODE_APPEND)) {
            output.write(line.getBytes(StandardCharsets.UTF_8));
        } catch (Exception ignored) { handler.post(this::disconnect); }
        tail.append(line);
        if (tail.length() > 24000) tail.delete(0, tail.length() - 24000);
    }
}
