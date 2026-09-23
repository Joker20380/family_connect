package com.familyconnect.app;

import android.app.*;
import android.os.*;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.*;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

/** Explicit opt-in restoration after updating a device which was already connected. */
@RunWith(AndroidJUnit4.class)
public class RestoreConnectionRuntimeTest {
    @Test public void restorePreviouslyConnectedDevice() throws Exception {
        assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcRestoreConnection")));
        Instrumentation ins=InstrumentationRegistry.getInstrumentation();String pkg=ins.getTargetContext().getPackageName();
        assumeTrue(pkg.endsWith(".friends"));
        try(ParcelFileDescriptor command=ins.getUiAutomation().executeShellCommand("am start -W -n "+pkg+"/com.familyconnect.app.FriendsActivity --ei tab 0")){
            try(InputStream in=new FileInputStream(command.getFileDescriptor())){while(in.read()!=-1){}}
        }
        AtomicReference<FriendsActivity> found=new AtomicReference<>();long until=SystemClock.elapsedRealtime()+10000;
        while(found.get()==null&&SystemClock.elapsedRealtime()<until){
            ins.runOnMainSync(()->{for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))if(a instanceof FriendsActivity)found.set((FriendsActivity)a);});
            if(found.get()==null)SystemClock.sleep(100);
        }
        assertNotNull(found.get());
        ins.runOnMainSync(()->{
            assertTrue("Existing activation must survive update",found.get().getPreferences(0).getBoolean("activated",false));
            if(ConnectionService.status.equals("off"))try{
                java.lang.reflect.Method toggle=FriendsActivity.class.getDeclaredMethod("toggle");toggle.setAccessible(true);toggle.invoke(found.get());
            }catch(Exception e){throw new AssertionError(e);}
        });
        until=SystemClock.elapsedRealtime()+45000;
        while(SystemClock.elapsedRealtime()<until&&!(ConnectionService.status.equals("on")&&ConnectionService.healthStatus.equals("ok")))SystemClock.sleep(300);
        assertEquals("on",ConnectionService.status);assertEquals("ok",ConnectionService.healthStatus);
    }
}
