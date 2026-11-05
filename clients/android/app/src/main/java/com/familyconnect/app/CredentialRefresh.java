package com.familyconnect.app;

import java.util.Arrays;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.function.Supplier;

final class CredentialRefresh {
    private final long owner;
    private long next;
    private boolean closed;
    private CompletableFuture<byte[]> pending;

    CredentialRefresh(long owner){this.owner=owner;}

    synchronized void poll(long current,long now,Supplier<CompletableFuture<byte[]>> fetch,Consumer<byte[]> deliver){
        if(closed||current!=owner)return;
        if(pending!=null){
            if(!pending.isDone())return;
            byte[] raw=null;
            try{raw=pending.getNow(null);if(raw!=null)deliver.accept(raw);}
            catch(RuntimeException rejected){}
            finally{if(raw!=null)Arrays.fill(raw,(byte)0);pending=null;}
        }
        if(now<next)return;
        next=now+30000;
        pending=fetch.get();
    }

    synchronized void close(){
        closed=true;
        if(pending!=null){pending.thenAccept(raw->{if(raw!=null)Arrays.fill(raw,(byte)0);});pending=null;}
    }
}
