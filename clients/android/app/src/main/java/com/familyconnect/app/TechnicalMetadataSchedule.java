package com.familyconnect.app;

final class TechnicalMetadataSchedule {
    private long next;
    private int failures;
    private boolean running;
    synchronized long delay(long now,boolean revoke){return running?1000:revoke&&failures==0?0:Math.max(0,next-now);}
    synchronized boolean begin(long now,boolean revoke){
        if(running||delay(now,revoke)>0)return false;
        running=true;return true;
    }
    synchronized void finish(long now,boolean success){
        running=false;failures=success?0:Math.min(6,failures+1);
        next=now+(success?60000:Math.min(1800000,60000L<<(failures-1)));
    }
    synchronized void revoke(){failures=0;next=0;}
}
