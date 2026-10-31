package com.familyconnect.app;

final class RadioCodec {
    static final int OPUS=16, C1600=7, C2400=8, C3200=9;
    static { System.loadLibrary("exit_audio"); }
    static native byte[] encode(short[] pcm, int mode);
    static native short[] decode(byte[] data, int mode);
    private RadioCodec() {}
}
