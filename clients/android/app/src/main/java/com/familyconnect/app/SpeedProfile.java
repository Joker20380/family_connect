package com.familyconnect.app;

import android.content.Context;

final class SpeedProfile {
    static boolean canSelect(String status,boolean busy) { return !busy&&"off".equals(status); }
    static int checked(int value) {
        if(value<0||value>2)throw new IllegalArgumentException("Invalid speed profile");
        return value;
    }
    static int read(Context context) {
        return checked(context.getSharedPreferences("mesh-session-profile",Context.MODE_PRIVATE).getInt("next",0));
    }
    static void save(Context context,int value) {
        if(!context.getSharedPreferences("mesh-session-profile",Context.MODE_PRIVATE).edit().putInt("next",checked(value)).commit())
            throw new IllegalStateException("Profile not saved");
    }
}
