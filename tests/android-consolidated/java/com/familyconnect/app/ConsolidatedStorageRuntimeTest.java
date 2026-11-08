package com.familyconnect.app;

import android.content.Context;
import android.app.AlertDialog;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.SystemClock;
import androidx.test.core.app.ActivityScenario;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.util.concurrent.Callable;
import java.util.concurrent.TimeUnit;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;

public class ConsolidatedStorageRuntimeTest {
    private final Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
    private final String sourceVersion=InstrumentationRegistry.getArguments().getString("sourceVersion");
    private <Value> Value worker(Callable<Value> action)throws Exception {
        return ChatRuntime.WORKER.submit(action).get(30,TimeUnit.SECONDS);
    }
    private File evidence(){return new File(context.getFilesDir(),"consolidated-storage.json");}
    private AlertDialog subscriptionDialog(){
        try{
            java.lang.reflect.Field field=SubscriptionUi.class.getDeclaredField("foregroundDialog");
            field.setAccessible(true);
            return (AlertDialog)field.get(null);
        }catch(ReflectiveOperationException failure){throw new AssertionError(failure);}
    }
    private void capture(AlertDialog dialog)throws Exception {
        android.view.View view=dialog.getWindow().getDecorView();
        assertTrue(view.getWidth()>0&&view.getHeight()>0);
        Bitmap screenshot=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);
        try(FileOutputStream output=new FileOutputStream(new File(context.getExternalFilesDir("ui-acceptance"),"consolidated-subscription-"+sourceVersion+".png"))){
            view.draw(new Canvas(screenshot));
            assertTrue(screenshot.compress(Bitmap.CompressFormat.PNG,100,output));
        }finally{screenshot.recycle();}
    }
    private android.content.SharedPreferences settings(){return context.getSharedPreferences(FriendsActivity.class.getName(),0);}
    @Before public void disposableOnly()throws Exception {
        assertEquals("true",InstrumentationRegistry.getArguments().getString("fc_disposable"));
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        assertEquals("com.familyconnect.app.friends",context.getPackageName());
        assertTrue("119".equals(sourceVersion)||"120".equals(sourceVersion)||"121".equals(sourceVersion));
        assertEquals("off",ConnectionService.status);
        if(android.os.Build.VERSION.SDK_INT>=33)assertEquals(android.content.pm.PackageManager.PERMISSION_GRANTED,
            context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS));
        assertFalse("Offline fixture must not contact real endpoints",new ChatNetworkAndroid(context).available());
    }
    @Test public void prepareHistoricalFormat()throws Exception {
        assertEquals(Integer.parseInt(sourceVersion),context.getPackageManager().getPackageInfo(context.getPackageName(),0).versionCode);
        assertFalse(evidence().exists());
        assertTrue(settings().edit().putBoolean("activated",true).putString("country","nl")
            .putString("gateway_id","nl-amsterdam-2").putString("transport","telemost").commit());
        assertTrue(context.getSharedPreferences("chat-notifications",0).edit().putBoolean("background",false).commit());
        assertEquals(AppVpnPolicy.all(),new AppVpnStore(context).read());
        JsonObject expected=new JsonObject();
        try(ControlIdentity identity=new FriendsIdentityVault(context).create()){
            expected.addProperty("identity",identity.reference());
        }
        worker(()->{
            try(ChatLocalAndroid chat=ChatLocalAndroid.open(context,true)){
                expected.add("profile",chat.call("profile",new JsonObject()));
                if(!sourceVersion.equals("120")){
                    long now=System.currentTimeMillis()/1000;
                    JsonObject response=new JsonObject();response.addProperty("schema",1);
                    response.addProperty("device",expected.get("identity").getAsString());
                    response.addProperty("observed_at",now);response.addProperty("cohort",true);
                    JsonObject snapshot=new JsonObject();snapshot.addProperty("state","active");
                    snapshot.addProperty("effective_state","active");snapshot.addProperty("paid_allow",true);
                    snapshot.addProperty("period_start",now-60);snapshot.addProperty("paid_until",now+3600);
                    snapshot.add("grace_until",com.google.gson.JsonNull.INSTANCE);
                    snapshot.addProperty("entitlement_until",now+3600);snapshot.addProperty("version",1);
                    snapshot.addProperty("updated_at",now-60);snapshot.addProperty("last_event_id","fixture-no-event");
                    response.add("subscription",snapshot);response.add("event",com.google.gson.JsonNull.INSTANCE);
                    JsonObject accepted=chat.acceptSubscription(response,expected.get("identity").getAsString());
                    assertTrue(accepted.get("accepted").getAsBoolean());
                    expected.addProperty("confirmed_at",now);
                }
            }
            return null;
        });
        expected.addProperty("uid",android.os.Process.myUid());
        expected.addProperty("first_install",context.getPackageManager().getPackageInfo(context.getPackageName(),0).firstInstallTime);
        Files.write(evidence().toPath(),expected.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    @Test public void verifyUpgradeAndSubscriptionScreen()throws Exception {
        assertEquals(122,context.getPackageManager().getPackageInfo(context.getPackageName(),0).versionCode);
        assertEquals(AppVpnPolicy.all(),new AppVpnStore(context).read());
        JsonObject expected=JsonParser.parseString(new String(Files.readAllBytes(evidence().toPath()),java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals(expected.get("uid").getAsInt(),android.os.Process.myUid());
        assertEquals(expected.get("first_install").getAsLong(),context.getPackageManager().getPackageInfo(context.getPackageName(),0).firstInstallTime);
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            assertEquals(expected.get("identity").getAsString(),identity.reference());
        }
        assertTrue(settings().getBoolean("activated",false));
        assertEquals("nl",settings().getString("country",""));
        assertEquals("nl-amsterdam-2",settings().getString("gateway_id",""));
        assertEquals("telemost",settings().getString("transport",""));
        worker(()->{
            try(ChatLocalAndroid chat=ChatLocalAndroid.open(context,false)){
                assertEquals(expected.get("profile"),chat.call("profile",new JsonObject()));
                JsonObject arguments=new JsonObject();arguments.add("device",expected.get("identity"));
                JsonObject view=chat.call("subscription_status",arguments).getAsJsonObject();
                assertTrue("Snapshot never invents a payment notice",view.get("notice").isJsonNull());
                if(!sourceVersion.equals("120")){
                    assertEquals(expected.get("confirmed_at"),view.get("confirmed_at"));
                    assertEquals("active",view.getAsJsonObject("snapshot").get("effective_state").getAsString());
                }else assertTrue(view.get("snapshot").isJsonNull());
            }
            return null;
        });
        String unavailable=SubscriptionUi.text(context).get("subscription_refresh_unavailable");
        String offline=SubscriptionUi.text(context).get("subscription_offline");
        try(ActivityScenario<FriendsActivity> scenario=ActivityScenario.launch(SubscriptionUi.intent(context))){
            java.util.concurrent.atomic.AtomicReference<String> rendered=new java.util.concurrent.atomic.AtomicReference<>("");
            long until=SystemClock.elapsedRealtime()+30000;
            while(SystemClock.elapsedRealtime()<until){
                scenario.onActivity(activity->{
                    AlertDialog dialog=subscriptionDialog();
                    if(dialog!=null&&dialog.isShowing()){
                        android.widget.TextView message=dialog.findViewById(android.R.id.message);
                        if(message!=null)rendered.set(message.getText().toString());
                    }
                });
                if(rendered.get().contains(unavailable)||rendered.get().contains(offline))break;
                SystemClock.sleep(200);
            }
            scenario.onActivity(activity->{
                AlertDialog dialog=subscriptionDialog();
                assertNotNull("Actual foreground subscription dialog",dialog);
                assertTrue(dialog.getWindow().getDecorView().hasWindowFocus());
                try{capture(dialog);}catch(Exception failure){throw new AssertionError(failure);}
            });
            assertTrue("Final offline outcome, not a loading screenshot: "+rendered.get(),rendered.get().contains(unavailable)||rendered.get().contains(offline));
            assertFalse("Cache is never a fresh server result",rendered.get().contains(SubscriptionUi.text(context).get("subscription_refresh_current")));
        }
    }
    @Test public void saveAppPolicyForRestart()throws Exception {
        new AppVpnStore(context).save(new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,
            java.util.Set.of(context.getPackageName()),java.util.Set.of("com.android.settings")));
    }
    @Test public void verifyAppPolicyAfterRestartOrReplacement()throws Exception {
        assertEquals(new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,java.util.Set.of(context.getPackageName()),
            java.util.Set.of("com.android.settings")),new AppVpnStore(context).read());
        JsonObject expected=JsonParser.parseString(new String(Files.readAllBytes(evidence().toPath()),java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals(expected.get("uid").getAsInt(),android.os.Process.myUid());
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            assertEquals(expected.get("identity").getAsString(),identity.reference());
        }
        assertTrue(settings().getBoolean("activated",false));
    }
}
