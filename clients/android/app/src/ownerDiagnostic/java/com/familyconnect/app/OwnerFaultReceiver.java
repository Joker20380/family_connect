package com.familyconnect.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class OwnerFaultReceiver extends BroadcastReceiver {
    private static native String control(String command);

    static String request(Intent intent) {
        String command = intent == null ? null : intent.getStringExtra("command");
        if ("correlation".equals(command)) {
            String body = intent.getStringExtra("request");
            return body != null && body.length() <= 16384 ? "correlation:" + body : null;
        }
        if (!"arm".equals(command) && !"status".equals(command) && !"disarm".equals(command)) {
            return null;
        }
        return command;
    }

    @Override public void onReceive(Context context, Intent intent) {
        String command = request(intent);
        if (command == null) {
            setResultCode(1);
            return;
        }
        try {
            NativeRestricted.load();
            setResultData(control(command));
            setResultCode(0);
        } catch (LinkageError error) {
            setResultCode(2);
        }
    }
}
