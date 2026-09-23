package com.familyconnect.app;

import android.app.*;
import android.content.*;
import android.os.SystemClock;
import android.service.notification.StatusBarNotification;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class ChatNotificationRuntimeTest {
    @org.junit.Before public void friendsVariantOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }
    private Notification await(Context c,String tag,int id){
        long until=SystemClock.uptimeMillis()+15000;
        while(SystemClock.uptimeMillis()<until){
            for(StatusBarNotification n:c.getSystemService(NotificationManager.class).getActiveNotifications())if(n.getId()==id&&java.util.Objects.equals(tag,n.getTag()))return n.getNotification();
            SystemClock.sleep(100);
        }
        return null;
    }
    @Test public void notificationUsesSavedNameAndHidesTextOnLockScreen(){
        Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
        NotificationManager manager=c.getSystemService(NotificationManager.class);
        assertTrue("Enable app notifications for device acceptance",manager.areNotificationsEnabled());
        String peer="abababababababababababababababab";JsonObject message=new JsonObject();message.addProperty("id","test-notification");message.addProperty("title","Test service notice");
        try{
            assertTrue(ChatNotifications.message(c,peer,message,false,"Проверка имени"));
            Notification found=await(c,"chat:"+peer,100);
            assertNotNull(found);assertEquals("Проверка имени",found.extras.getString(Notification.EXTRA_TITLE));
            assertEquals(Notification.VISIBILITY_PRIVATE,found.visibility);assertNotNull(found.publicVersion);assertNotNull(found.contentIntent);
            assertTrue(ChatNotifications.message(c,peer,message,false,"Новое имя"));
            int count=0;for(StatusBarNotification n:manager.getActiveNotifications())if(("chat:"+peer).equals(n.getTag()))count++;
            assertEquals("Same conversation replaces the existing notification",1,count);
        }finally{ChatNotifications.cancel(c,peer);}
    }
    @Test public void serviceNoticeHasSeparateChannelAndOpensMessenger()throws Exception{
        Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();JsonObject message=new JsonObject();message.addProperty("title","Проверка уведомления");
        try{
            assertTrue(ChatNotifications.message(c,"service",message,true,null));
            Notification found=await(c,"chat:service",100);
            assertNotNull(found);assertEquals(ChatNotifications.EVENTS,found.getChannelId());assertEquals("Family Connect",found.extras.getString(Notification.EXTRA_TITLE));
            assertEquals(c.getPackageName(),found.contentIntent.getCreatorPackage());
        }finally{ChatNotifications.cancel(c,"service");}
    }
    @Test public void deliveryRemainsVisibleAfterActivityBackgrounded()throws Exception{
        org.junit.Assume.assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcActiveDeviceCheck")));
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
        Instrumentation i=InstrumentationRegistry.getInstrumentation();Context c=i.getTargetContext();
        try(android.os.ParcelFileDescriptor command=i.getUiAutomation().executeShellCommand("am start -n "+c.getPackageName()+"/com.familyconnect.app.FriendsActivity")){
            try(java.io.FileInputStream input=new java.io.FileInputStream(command.getFileDescriptor())){while(input.read()!=-1){}}
        }
        SystemClock.sleep(2000);
        assertTrue("Background delivery must be enabled",ChatDeliveryService.enabled(c));
        i.runOnMainSync(()->{
            assertFalse("An activity must be resumed",androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED).isEmpty());
            for(Activity activity:androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED)){
                assertTrue("Active device required",activity.getPreferences(Context.MODE_PRIVATE).getBoolean("activated",false));
                ChatDeliveryService.start(activity);
            }
        });
        assertNotNull("Foreground service must start before leaving the activity: "+ChatDeliveryService.startFailure+" running="+ChatDeliveryService.running,await(c,null,42));
        i.runOnMainSync(()->{
            for(Activity activity:androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED))activity.moveTaskToBack(true);
        });
        SystemClock.sleep(7000);
        boolean found=false;for(StatusBarNotification n:c.getSystemService(NotificationManager.class).getActiveNotifications())if(n.getId()==42){found=true;assertTrue((n.getNotification().flags&Notification.FLAG_FOREGROUND_SERVICE)!=0);}
        assertTrue("Messenger delivery must remain active when the screen is closed",found);
        assertNotNull(ChatRuntime.WORKER.submit(()->ChatRuntime.open(c,false).call("profile",new JsonObject())).get(30,java.util.concurrent.TimeUnit.SECONDS));
    }
}
