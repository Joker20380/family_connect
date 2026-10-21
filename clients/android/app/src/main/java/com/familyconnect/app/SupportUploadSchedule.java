package com.familyconnect.app;

final class SupportUploadSchedule {
    private boolean running;
    private long next;

    synchronized boolean start(long now, boolean consented) {
        if (!consented || running || now < next) return false;
        running = true;
        return true;
    }

    synchronized void finish(long now, boolean success) {
        next = now + (success ? 60000 : 300000);
        running = false;
    }
}
