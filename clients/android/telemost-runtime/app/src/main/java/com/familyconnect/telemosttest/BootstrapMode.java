package com.familyconnect.telemosttest;

import java.nio.charset.StandardCharsets;

final class BootstrapMode {
    static String parse(byte[] raw, String control) {
        if (raw == null) return "";
        if (raw.length > 16) throw new IllegalArgumentException("bootstrap mode rejected");
        String mode = new String(raw, StandardCharsets.UTF_8).trim();
        if (!mode.equals("refresh") && !mode.equals("recover")) throw new IllegalArgumentException("bootstrap mode rejected");
        if (control == null || !control.startsWith("https://")) throw new IllegalArgumentException("control required");
        if (mode.equals("recover") && !control.equals("https://127.0.0.1:1")) throw new IllegalArgumentException("control guard required");
        return mode;
    }
}
