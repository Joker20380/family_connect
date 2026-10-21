package com.familyconnect.app;

final class SupportAccess {
    private long until;
    synchronized void enable(long now){until=now+3600000;}
    synchronized void disable(){until=0;}
    synchronized boolean active(long now){return now>=0&&until>now;}
    synchronized boolean allows(int uid,long now){return uid==2000&&active(now);}
}
