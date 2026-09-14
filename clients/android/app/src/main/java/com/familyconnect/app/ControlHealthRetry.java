package com.familyconnect.app;

import java.util.function.BooleanSupplier;
import java.util.function.LongSupplier;

/** Allow Android's VPN Network to settle within the existing health deadline. */
final class ControlHealthRetry {
    interface Sleep { void pause(long milliseconds) throws InterruptedException; }
    static boolean check(BooleanSupplier probe, BooleanSupplier cancelled, LongSupplier monotonic,
                         Sleep sleep, long budget) throws InterruptedException {
        long start=monotonic.getAsLong();
        while(!cancelled.getAsBoolean() && monotonic.getAsLong()-start<budget) {
            if(probe.getAsBoolean())
                return !cancelled.getAsBoolean() && monotonic.getAsLong()-start<budget;
            long remaining=budget-(monotonic.getAsLong()-start);
            if(cancelled.getAsBoolean() || remaining<=0)return false;
            sleep.pause(Math.min(100,remaining));
        }
        return false;
    }
}
