package com.familyconnect.telemosttest;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

public final class ProbeActivity extends Activity {
    private ProbeService service;
    private EditText room;
    private TextView status;
    private final Handler handler = new Handler();
    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            if (service != null) status.setText((service.active() ? "RUNNING\n" : "IDLE\n") + service.snapshot());
            handler.postDelayed(this, 1000);
        }
    };
    private final ServiceConnection connection = new ServiceConnection() {
        @Override public void onServiceConnected(ComponentName name, IBinder binder) {
            service = ((ProbeService.LocalBinder) binder).service();
            service.lifecycle("activity_bound");
            if (getIntent().getBooleanExtra("disconnect", false)) service.disconnect();
            if (getIntent().getBooleanExtra("run", false)) {
                getIntent().removeExtra("run");
                startProbe();
            }
        }
        @Override public void onServiceDisconnected(ComponentName name) { service = null; }
    };

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (intent.getBooleanExtra("disconnect", false) && service != null) service.disconnect();
        if (intent.getBooleanExtra("close", false)) finish();
        if (intent.getBooleanExtra("recreate", false)) {
            intent.removeExtra("recreate");
            recreate();
        }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(24, 24, 24, 24);
        TextView title = new TextView(this);
        title.setText("Telemost 5N.2 — synthetic binary only\nNo TUN / no Family E2E / no protected sockets\nDisable any VPN before starting. Back stops; Home keeps testing.");
        layout.addView(title);
        room = new EditText(this);
        room.setHint("Disposable HTTPS room (not saved)");
        room.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        room.setSaveEnabled(false);
        room.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO_EXCLUDE_DESCENDANTS);
        layout.addView(room);
        Button start = new Button(this);
        start.setText("Connect + run VP8 binary suite");
        start.setOnClickListener(view -> startProbe());
        layout.addView(start);
        Button stop = new Button(this);
        stop.setText("Disconnect");
        stop.setOnClickListener(view -> { if (service != null) service.disconnect(); });
        layout.addView(stop);
        status = new TextView(this);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(status);
        layout.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
        bindService(new Intent(this, ProbeService.class), connection, Context.BIND_AUTO_CREATE);
    }

    private void startProbe() {
        if (service == null || service.active()) return;
        String value = room.getText().toString().trim();
        room.setText("");
        File input = new File(getFilesDir(), "room.input");
        try {
            if (value.isEmpty() && input.isFile() && input.length() <= 2048) value = new String(Files.readAllBytes(input.toPath()), StandardCharsets.UTF_8).trim();
        } catch (Exception ignored) { status.setText("ROOM_INPUT_FAILED"); }
        finally { input.delete(); }
        service.startProbe(value);
    }

    @Override protected void onResume() {
        super.onResume();
        if (service != null) service.lifecycle("foreground");
        handler.post(refresh);
    }
    @Override protected void onPause() {
        handler.removeCallbacks(refresh);
        if (service != null) service.lifecycle("background");
        super.onPause();
    }
    @Override protected void onDestroy() {
        handler.removeCallbacks(refresh);
        if (isFinishing() && service != null) service.disconnect();
        unbindService(connection);
        super.onDestroy();
    }
}
