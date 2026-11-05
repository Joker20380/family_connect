package com.familyconnect.app;

import android.os.Build;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;

public class CredentialRefreshRuntimeTest {
    @Before public void isolatedOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
        assertTrue(Build.FINGERPRINT.contains("generic")||Build.MODEL.contains("sdk"));
    }
    @Test public void nativeRenewalRejectsAbsentAndLateOwner(){
        NativeRestricted.load();
        assertFalse(NativeRestricted.renew(0,new byte[]{1},new byte[64]));
        assertFalse(NativeRestricted.renew(Long.MAX_VALUE,new byte[]{1},new byte[64]));
        assertFalse(NativeRestricted.renew(1,null,new byte[64]));
    }
    @Test public void ownerDispatchAndDisconnectOnSupportedApis(){
        CredentialRefresh owner=new CredentialRefresh(12);CompletableFuture<byte[]> pending=new CompletableFuture<>();AtomicInteger delivered=new AtomicInteger();
        owner.poll(12,0,()->pending,raw->delivered.incrementAndGet());
        owner.poll(13,1,()->{throw new AssertionError();},raw->delivered.incrementAndGet());
        owner.close();byte[] material={2,4};pending.complete(material);
        assertEquals(0,delivered.get());assertArrayEquals(new byte[2],material);assertFalse(pending.isCancelled());
    }
    @Test public void selectedGatewayAndPrewarmRemainSeparate(){
        assertNotEquals(RestrictedGateway.namespace(RestrictedGateway.PRIMARY),RestrictedGateway.namespace(RestrictedGateway.SECONDARY));
        CredentialRefresh active=new CredentialRefresh(21),previous=new CredentialRefresh(20);
        CompletableFuture<byte[]> old=new CompletableFuture<>();previous.poll(20,0,()->old,raw->{throw new AssertionError();});previous.close();
        AtomicInteger count=new AtomicInteger();byte[] fresh={9};
        active.poll(21,0,()->CompletableFuture.completedFuture(fresh),raw->{throw new AssertionError();});
        active.poll(21,1,()->{throw new AssertionError();},raw->{assertEquals(9,raw[0]);count.incrementAndGet();});
        byte[] stale={3};old.complete(stale);assertEquals(1,count.get());assertEquals(0,stale[0]);assertEquals(0,fresh[0]);active.close();
    }
}
