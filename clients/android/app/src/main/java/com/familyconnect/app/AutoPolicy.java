package com.familyconnect.app;
final class AutoPolicy {
    private int next=0,failures=0;
    Transport next(){failures=0;return next<3?Transport.values()[next++]:null;}
    boolean advance(boolean healthy){if(healthy){failures=0;return false;}return ++failures>=2;}
}
