package com.familyconnect.app;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerPermissionTest {
    @Test public void dumpDeniedForUnprivilegedCaller() throws Exception {
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertEquals("com.familyconnect.app.friends.test",context.getPackageName());
        assertNotEquals(10283,android.os.Process.myUid());
        assertEquals(PackageManager.PERMISSION_DENIED,context.checkSelfPermission("android.permission.DUMP"));
        ComponentName receiver=new ComponentName("com.familyconnect.app.friends","com.familyconnect.app.OwnerFaultReceiver");
        assertEquals("android.permission.DUMP",context.getPackageManager().getReceiverInfo(receiver,0).permission);
        CountDownLatch completed=new CountDownLatch(1);
        AtomicInteger result=new AtomicInteger(-927);
        AtomicReference<String> data=new AtomicReference<>();
        Intent request=new Intent().setComponent(receiver).putExtra("command","status");
        context.sendOrderedBroadcast(request,null,new BroadcastReceiver(){
            @Override public void onReceive(Context observed,Intent intent){
                result.set(getResultCode());data.set(getResultData());completed.countDown();
            }
        },new Handler(Looper.getMainLooper()),-927,null,null);
        assertTrue(completed.await(15,TimeUnit.SECONDS));
        assertEquals(-927,result.get());assertNull(data.get());
        Bundle evidence=new Bundle();
        evidence.putString("owner_evidence","{\"dump_enforced\":true,\"caller_uid\":"+android.os.Process.myUid()+",\"command\":\"status\"}");
        InstrumentationRegistry.getInstrumentation().sendStatus(2,evidence);
    }
}
