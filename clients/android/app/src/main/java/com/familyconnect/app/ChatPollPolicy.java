package com.familyconnect.app;

/** Foreground mailbox discovery; retries/backoff remain owned by DeliveryController. */
final class ChatPollPolicy {
    private long next;
    boolean poll(long now,boolean visible,boolean online,boolean running,boolean pending,boolean healthy){
        if(!visible||!online||running||pending||!healthy||now<next)return false;
        next=now+6000;return true;
    }
}
