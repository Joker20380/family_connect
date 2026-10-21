package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class SupportUploadScheduleTest {
    @Test public void startsOnlyWithConsent() {
        SupportUploadSchedule schedule = new SupportUploadSchedule();
        assertFalse(schedule.start(0, false));
        assertTrue(schedule.start(0, true));
    }

    @Test public void singleWorkerWithoutQueuedTicks() {
        SupportUploadSchedule schedule = new SupportUploadSchedule();
        assertTrue(schedule.start(1000, true));
        assertFalse(schedule.start(120000, true));
        schedule.finish(120000, true);
        assertFalse(schedule.start(120001, true));
    }

    @Test public void latencyVariationCannotShortenServerInterval() {
        SupportUploadSchedule schedule = new SupportUploadSchedule();
        assertTrue(schedule.start(0, true));
        long firstStored = 14000;
        schedule.finish(15000, true);
        assertTrue(60000 - firstStored < 60000);
        assertFalse(schedule.start(60000, true));
        assertFalse(schedule.start(74999, true));
        assertTrue(schedule.start(75000, true));
        assertTrue(75000 - firstStored >= 60000);
    }

    @Test public void failureBackoffStartsAtCompletion() {
        SupportUploadSchedule schedule = new SupportUploadSchedule();
        assertTrue(schedule.start(0, true));
        schedule.finish(15000, false);
        assertFalse(schedule.start(314999, true));
        assertTrue(schedule.start(315000, true));
    }

    @Test public void revokedConsentCannotStartAfterCooldown() {
        SupportUploadSchedule schedule = new SupportUploadSchedule();
        assertTrue(schedule.start(0, true));
        schedule.finish(1000, true);
        assertFalse(schedule.start(61000, false));
        assertTrue(schedule.start(61000, true));
    }
}
