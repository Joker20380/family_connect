package com.familyconnect.app;

import android.content.Context;
import org.json.JSONObject;

final class StartupDiagnostics {
    static void begin(Context context, long handle) {}
    static void capture(Context context, long handle, JSONObject stats) {}
    static void stopped(Context context, long handle) {}
    static ConnectivityOrchestrator.Rejected rejected(long handle, ConnectivityOrchestrator.Failure category) {
        return new ConnectivityOrchestrator.Rejected(category);
    }
}
