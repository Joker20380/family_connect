package com.familyconnect.app;
import android.os.Bundle;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;
@RunWith(AndroidJUnit4.class)
public class DeviceAdminRuntimeTest {
 @Test public void existingIdentityAndRole() throws Exception {
  assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcAdminCheck")));
  android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
  try(ControlIdentity identity=new FriendsIdentityVault(context).load()) {
   Bundle result=new Bundle();result.putString("device",identity.reference());InstrumentationRegistry.getInstrumentation().sendStatus(0,result);
   if("true".equals(InstrumentationRegistry.getArguments().getString("fcExpectAdmin"))) {
    com.google.gson.JsonObject role=new FriendsAccessAndroid(context,true).noticeRole();
    assertEquals(identity.reference(),role.get("device").getAsString());assertEquals("administrator",role.get("role").getAsString());
    assertTrue(new FriendsAccessAndroid(context,true).listNotices(0).has("events"));
   }
  }
 }
 private boolean text(android.view.View view,String expected){
  if(view instanceof android.widget.TextView&&expected.contentEquals(((android.widget.TextView)view).getText()))return true;
  if(view instanceof android.view.ViewGroup)for(int i=0;i<((android.view.ViewGroup)view).getChildCount();i++)if(text(((android.view.ViewGroup)view).getChildAt(i),expected))return true;
  return false;
 }
 private boolean click(android.view.View view,String expected){
  if(view instanceof android.widget.Button&&expected.contentEquals(((android.widget.Button)view).getText()))return view.performClick();
  if(view instanceof android.view.ViewGroup)for(int i=0;i<((android.view.ViewGroup)view).getChildCount();i++)if(click(((android.view.ViewGroup)view).getChildAt(i),expected))return true;
  return false;
 }
 @Test public void administratorScreenWithinChat() throws Exception {
  assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcExpectAdmin")));
  android.app.Instrumentation ins=InstrumentationRegistry.getInstrumentation();android.content.Context context=ins.getTargetContext();
  try(android.os.ParcelFileDescriptor command=ins.getUiAutomation().executeShellCommand("am start -W -n "+context.getPackageName()+"/com.familyconnect.app.FriendsActivity --ei tab 1")){
   try(java.io.InputStream in=new java.io.FileInputStream(command.getFileDescriptor())){while(in.read()!=-1){}}
  }
  java.util.concurrent.atomic.AtomicReference<ChatActivity> activity=new java.util.concurrent.atomic.AtomicReference<>();
  long until=android.os.SystemClock.elapsedRealtime()+25000;
  while(activity.get()==null&&android.os.SystemClock.elapsedRealtime()<until){
   ins.runOnMainSync(()->{for(android.app.Activity a:androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED))if(a instanceof ChatActivity)try{
    java.lang.reflect.Field busy=ChatActivity.class.getDeclaredField("busy");busy.setAccessible(true);
    java.lang.reflect.Field chat=ChatActivity.class.getDeclaredField("chat");chat.setAccessible(true);
    if(!busy.getBoolean(a)&&chat.get(a)!=null)activity.set((ChatActivity)a);
   }catch(Exception e){throw new AssertionError(e);}});android.os.SystemClock.sleep(200);
  }
  assertNotNull(activity.get());
  ins.runOnMainSync(()->{try{java.lang.reflect.Method m=ChatActivity.class.getDeclaredMethod("noticeAdmin");m.setAccessible(true);m.invoke(activity.get());}catch(Exception e){throw new AssertionError(e);}});
  java.util.concurrent.atomic.AtomicBoolean ready=new java.util.concurrent.atomic.AtomicBoolean();until=android.os.SystemClock.elapsedRealtime()+25000;
  while(!ready.get()&&android.os.SystemClock.elapsedRealtime()<until){ins.runOnMainSync(()->ready.set(text(activity.get().getWindow().getDecorView(),context.getString(R.string.notice_admin_active))));android.os.SystemClock.sleep(200);}
  assertTrue("Server verified administrator visible in chat",ready.get());
  com.google.gson.JsonArray records=new FriendsAccessAndroid(context,true).listNotices(0).getAsJsonArray("events");
  if(!records.isEmpty()){
   com.google.gson.JsonObject event=records.get(0).getAsJsonObject();
   ins.runOnMainSync(()->{try{
    java.lang.reflect.Field title=ChatActivity.class.getDeclaredField("announcementTitle"),body=ChatActivity.class.getDeclaredField("announcementBody");title.setAccessible(true);body.setAccessible(true);title.set(activity.get(),event.get("title").getAsString());body.set(activity.get(),event.get("body").getAsString());
    java.lang.reflect.Method method=ChatActivity.class.getDeclaredMethod("noticeCompose",com.google.gson.JsonObject.class);method.setAccessible(true);method.invoke(activity.get(),event);
    assertTrue(text(activity.get().getWindow().getDecorView(),event.get("title").getAsString()));
    click(activity.get().getWindow().getDecorView(),context.getString(R.string.notice_preview));
    assertTrue(text(activity.get().getWindow().getDecorView(),context.getString(R.string.notice_save_edit)));
    assertFalse(text(activity.get().getWindow().getDecorView(),context.getString(R.string.notice_publish)));
   }catch(Exception error){throw new AssertionError(error);}});
  }


 }

}
