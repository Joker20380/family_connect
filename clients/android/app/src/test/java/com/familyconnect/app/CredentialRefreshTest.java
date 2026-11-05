package com.familyconnect.app;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import static org.junit.Assert.*;

public class CredentialRefreshTest {
    @Test public void oneFlightAndBoundedOwnerPolling(){
        CredentialRefresh refresh=new CredentialRefresh(7);
        CompletableFuture<byte[]> result=new CompletableFuture<>();AtomicInteger fetches=new AtomicInteger(),deliveries=new AtomicInteger();
        for(int index=0;index<100;index++)refresh.poll(7,index,()->{fetches.incrementAndGet();return result;},raw->deliveries.incrementAndGet());
        assertEquals(1,fetches.get());assertEquals(0,deliveries.get());
        byte[] material={1,2,3};result.complete(material);
        refresh.poll(7,100,()->{throw new AssertionError();},raw->{assertEquals(1,raw[0]);deliveries.incrementAndGet();});
        assertArrayEquals(new byte[3],material);assertEquals(1,deliveries.get());
        refresh.poll(7,29999,()->{throw new AssertionError();},raw->{throw new AssertionError();});
        refresh.close();
    }
    @Test public void disconnectDiscardsLateDeliveryWithoutCancellingSharedFetch(){
        CredentialRefresh refresh=new CredentialRefresh(7);CompletableFuture<byte[]> result=new CompletableFuture<>();
        refresh.poll(7,0,()->result,raw->{throw new AssertionError();});refresh.close();
        assertFalse(result.isCancelled());byte[] raw={7,8};result.complete(raw);assertArrayEquals(new byte[2],raw);
        refresh.poll(7,30000,()->{throw new AssertionError();},value->{throw new AssertionError();});
    }
    @Test public void otherOwnerCannotReceivePendingMaterials(){
        CredentialRefresh refresh=new CredentialRefresh(7);CompletableFuture<byte[]> result=new CompletableFuture<>();
        refresh.poll(7,0,()->result,raw->{throw new AssertionError();});byte[] raw={1};result.complete(raw);
        refresh.poll(8,100,()->{throw new AssertionError();},value->{throw new AssertionError();});
        assertEquals(1,raw[0]);refresh.close();assertEquals(0,raw[0]);
    }
    @Test public void failedOrEmptyRefreshDoesNotDeliverOrRetryImmediately(){
        for(boolean failed:new boolean[]{true,false}){
            CredentialRefresh refresh=new CredentialRefresh(9);CompletableFuture<byte[]> result=new CompletableFuture<>();
            refresh.poll(9,0,()->result,raw->{throw new AssertionError();});
            if(failed)result.completeExceptionally(new IllegalStateException());else result.complete(null);
            refresh.poll(9,1,()->{throw new AssertionError();},raw->{throw new AssertionError();});
            refresh.close();
        }
    }
}
