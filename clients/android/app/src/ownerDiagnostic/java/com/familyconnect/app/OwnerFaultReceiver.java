package com.familyconnect.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public final class OwnerFaultReceiver extends BroadcastReceiver {
    private static native String control(String command);

    @Override public void onReceive(Context context, Intent intent) {
        String command = intent == null ? null : intent.getStringExtra("command");
        if (!"arm".equals(command) && !"status".equals(command) && !"disarm".equals(command)) {
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
