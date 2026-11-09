package com.familyconnect.app;

import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import androidx.test.core.app.ActivityScenario;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class AppVpnRejectedPolicyTest {
    @Test public void invalidIncludeThenAllDisconnectConnectWithoutRestart()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        AwgRuntimeTest helper=new AwgRuntimeTest();Context context=helper.context;
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        helper.clean();helper.shell("appops set "+context.getPackageName()+" ACTIVATE_VPN allow");
        if(android.os.Build.VERSION.SDK_INT>=33)helper.shell("pm grant "+context.getPackageName()+" android.permission.POST_NOTIFICATIONS");
        AppVpnStore store=new AppVpnStore(context);AppVpnPolicy previous=store.read();
        ProfileStore profile=new ProfileStore(context,Transport.TCP);String oldProfile=profile.exists()?profile.load():null;
        android.content.SharedPreferences preferences=context.getSharedPreferences(MainActivity.class.getName(),0);
        boolean previousAuto=preferences.getBoolean("auto",true);String previousTransport=preferences.getString("transport","wg");
        Intent disconnect=new Intent(context,ConnectionService.class).setAction("disconnect");
        try{
            preferences.edit().putBoolean("auto",false).putString("transport","tcp").commit();
            profile.save(TcpRuntimeTest.profile());store.save(AppVpnPolicy.all());
            saveMode(1);assertTrue(store.read().selected().isEmpty());clickConnect();
            assertTrue("Rejected policy is explained",ConnectionService.failed);
            saveMode(0);context.startService(disconnect);SystemClock.sleep(500);clickConnect();helper.waitState("on");
            context.startService(disconnect);helper.waitState("off");helper.clean();
            store.save(new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,java.util.Set.of("not.available.saved.package"),java.util.Set.of()));
            saveMode(1);clickConnect();waitOff();assertTrue(ConnectionService.failed);
            try{
                helper.shell("pm disable-user --user 0 com.familyconnect.appprobe.alpha");
                store.save(new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,java.util.Set.of("com.familyconnect.appprobe.alpha"),java.util.Set.of()));
                saveMode(1);clickConnect();waitOff();assertTrue(ConnectionService.failed);
            }finally{helper.shell("pm enable com.familyconnect.appprobe.alpha");}
            saveMode(0);context.startService(disconnect);helper.waitState("off");SystemClock.sleep(500);
            profile.save("invalid synthetic profile");clickConnect();waitOff();assertTrue(ConnectionService.failed);
            ControlOperations.APP.requireIdle();profile.save(TcpRuntimeTest.profile());
            clickConnect();helper.waitState("on");assertFalse(ConnectionService.failed);
            context.startService(disconnect);helper.waitState("off");helper.clean();
            Object retainedOwner=new Object();ControlOperations.APP.claim(retainedOwner);
            AppVpnPolicy retainedPolicy=AppVpnPolicy.all();ConnectionService.activeApplications=retainedPolicy;ConnectionService.status="cleanup-required";
            try{
                context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","tcp"));
                SystemClock.sleep(1000);ControlOperations.APP.requireOwner(retainedOwner);
                assertEquals("cleanup-required",ConnectionService.status);assertSame(retainedPolicy,ConnectionService.activeApplications);
            }finally{ControlOperations.APP.session(retainedOwner,()->{ControlOperations.APP.release(retainedOwner);ConnectionService.activeApplications=null;ConnectionService.status="off";});}
            try(var output=context.openFileOutput("app-vpn-rejection.json",Context.MODE_PRIVATE)){
                output.write(("{\"api\":"+android.os.Build.VERSION.SDK_INT+",\"ui_service_reconnect\":true,\"process_restart\":false,\"disabled_missing\":true,\"postclaim_error\":true,\"busy_owner_preserved\":true}").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            }
        }finally{
            context.startService(disconnect);store.save(previous);
            preferences.edit().putBoolean("auto",previousAuto).putString("transport",previousTransport).commit();
            if(oldProfile==null)profile.clear();else profile.save(oldProfile);
        }
    }
    private void saveMode(int mode)throws Exception{
        try(ActivityScenario<AppVpnActivity> screen=ActivityScenario.launch(AppVpnActivity.class)){
            screen.onActivity(activity->((android.widget.Spinner)activity.getWindow().getDecorView().findViewWithTag("app_vpn_modes")).setSelection(mode));
            InstrumentationRegistry.getInstrumentation().waitForIdleSync();
            screen.onActivity(activity->activity.getWindow().getDecorView().findViewWithTag("app_vpn_save").performClick());
        }
    }
    private void waitOff()throws Exception{
        long deadline=SystemClock.elapsedRealtime()+15000;
        while(!"off".equals(ConnectionService.status)&&SystemClock.elapsedRealtime()<deadline)SystemClock.sleep(100);
        assertEquals("Released resources after rejected attempt","off",ConnectionService.status);
        ControlOperations.APP.requireIdle();
    }
    private void clickConnect()throws Exception{
        try(ActivityScenario<MainActivity> screen=ActivityScenario.launch(MainActivity.class)){
            screen.onActivity(activity->{
                try{
                    java.lang.reflect.Field button=MainActivity.class.getDeclaredField("toggle");button.setAccessible(true);
                    assertTrue(((android.view.View)button.get(activity)).performClick());
                }catch(ReflectiveOperationException error){throw new AssertionError(error);}
            });
            InstrumentationRegistry.getInstrumentation().waitForIdleSync();SystemClock.sleep(400);
        }
    }
}
