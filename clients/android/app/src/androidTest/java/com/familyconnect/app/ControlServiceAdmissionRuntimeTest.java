package com.familyconnect.app;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import java.io.File;
import java.security.KeyStore;
import java.util.function.BooleanSupplier;
import org.junit.Before;
import org.junit.After;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Actual service admission/lifecycle, empty debug pilot only. No tunnel or fixtures installed. */
@RunWith(AndroidJUnit4.class)
public class ControlServiceAdmissionRuntimeTest {
    private Context context;
    private MainActivity activity;
    private boolean admitted;
    private void empty() throws Exception {
        for(Transport transport:Transport.values())assertFalse(new ProfileStore(context,transport).present());
        KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
        for(String name:new String[]{"identity","journal","enrollment"}){
            assertFalse(keys.containsAlias("family-connect-control-"+name+"-v1"));
            for(String suffix:new String[]{"",".bak",".new"})
                assertFalse(new File(context.getNoBackupFilesDir(),"control-"+name+".enc"+suffix).exists());
        }
    }
    @SuppressWarnings("deprecation")
    private boolean serviceRunning() {
        for(ActivityManager.RunningServiceInfo service:context.getSystemService(ActivityManager.class).getRunningServices(Integer.MAX_VALUE))
            if(ConnectionService.class.getName().equals(service.service.getClassName()))return true;
        return false;
    }
    private boolean idle() {
        try {ControlOperations.APP.requireIdle();return true;}
        catch(java.io.IOException busy){return false;}
    }
    private void await(BooleanSupplier condition) {
        long deadline=SystemClock.elapsedRealtime()+10000;
        while(!condition.getAsBoolean()&&SystemClock.elapsedRealtime()<deadline)SystemClock.sleep(50);
        assertTrue("Service did not reach expected state",condition.getAsBoolean());
    }
    @Before public void enter() throws Exception {
        context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertEquals("com.familyconnect.app.pilot",context.getPackageName());
        assertTrue((context.getApplicationInfo().flags&ApplicationInfo.FLAG_DEBUGGABLE)!=0);
        assertEquals("true",InstrumentationRegistry.getArguments().getString("fc_disposable"));
        ControlOperations.APP.requireIdle();assertEquals("off",ConnectionService.status);assertFalse(serviceRunning());empty();
        // @After must not stop a pre-existing service if any prerequisite fails.
        admitted=true;
        activity=(MainActivity)InstrumentationRegistry.getInstrumentation().startActivitySync(
            new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();
    }
    @After public void leave() throws Exception {
        if(!admitted)return;
        context.stopService(new Intent(context,ConnectionService.class));
        await(()->"off".equals(ConnectionService.status)&&!serviceRunning()&&idle());
        ControlOperations.APP.requireIdle();empty();
        if(activity!=null)InstrumentationRegistry.getInstrumentation().runOnMainSync(()->activity.finish());
    }
    private void rejected(Intent request) throws Exception {
        long before=ConnectionService.controlResultId;
        context.startForegroundService(request);
        await(()->ConnectionService.controlResultId>before);
        assertEquals("FAILED",ConnectionService.controlOutcome);
        await(()->"off".equals(ConnectionService.status)&&!serviceRunning()&&idle());
        ControlOperations.APP.requireIdle();empty();
    }
    @Test public void invalidGatewayRejectedBeforeIdentityCreation() throws Exception {
        rejected(new Intent(context,ConnectionService.class).setAction("select-gateway").putExtra("gateway","invalid/id"));
    }
    @Test public void unenrolledSelectionReleasesOwnerAndCanBeRetried() throws Exception {
        for(int attempt=0;attempt<2;attempt++)
            rejected(new Intent(context,ConnectionService.class).setAction("select-gateway").putExtra("gateway","test-gateway"));
    }
    @Test public void cancelledPermissionCallbackDoesNotStartSelection() throws Exception {
        var pending=MainActivity.class.getDeclaredField("pendingGateway");pending.setAccessible(true);
        long before=ConnectionService.controlResultId;
        InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{
            try {pending.set(activity,"test-gateway");activity.onActivityResult(20,Activity.RESULT_CANCELED,null);}
            catch(Exception e){throw new AssertionError(e);}
        });
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();SystemClock.sleep(500);
        assertNull(pending.get(activity));assertEquals(before,ConnectionService.controlResultId);
        assertEquals("off",ConnectionService.status);ControlOperations.APP.requireIdle();empty();
    }
}
