package com.familyconnect.app;

import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.service.notification.StatusBarNotification;
import android.view.accessibility.AccessibilityNodeInfo;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.google.gson.JsonObject;
import java.io.File;
import java.nio.file.Files;
import java.security.KeyStore;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class SubscriptionRuntimeTest {
    private final Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
    private final Bundle arguments=InstrumentationRegistry.getArguments();
    private <Value> Value worker(Callable<Value> action)throws Exception{return ChatRuntime.WORKER.submit(action).get(40,TimeUnit.SECONDS);}

    @Before public void disposableOnly(){
        assertTrue(context.getPackageName().equals("com.familyconnect.app.subscriptiontest")||context.getPackageName().equals("com.familyconnect.app.subscriptionnatural.friends"));
        assertEquals("true",arguments.getString("fc_disposable"));
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        assertEquals("off",ConnectionService.status);
        AppLanguage.select(context,arguments.getString("language","en"));
    }

    private JsonObject refresh()throws Exception{
        CompletableFuture<JsonObject> response=new CompletableFuture<>();
        SubscriptionRefreshGate.Request request=ChatRuntime.SUBSCRIPTION_REFRESH.begin();assertNotNull(request);
        ChatRuntime.refreshSubscription(context,request,response::complete);
        JsonObject result=response.get(40,TimeUnit.SECONDS);
        assertEquals("Refresh result",arguments.getString("outcome","current"),result.get("refresh_status").getAsString());
        verify(result);
        return result;
    }

    private void verify(JsonObject view)throws Exception{
        String state=arguments.getString("state");
        if("outside".equals(state)){
            assertFalse(view.get("cohort").getAsBoolean());assertTrue(view.get("snapshot").isJsonNull());
        }else if(state!=null){
            JsonObject snapshot=view.getAsJsonObject("snapshot");
            assertEquals(state,snapshot.get("effective_state").getAsString());
            assertTrue(snapshot.get("paid_until").getAsLong()>snapshot.get("period_start").getAsLong());
        }
        String event=arguments.getString("event");
        if("none".equals(event))assertTrue(view.get("notice").isJsonNull());
        else if(event!=null)assertEquals(event,view.getAsJsonObject("notice").get("subscription_event").getAsString());
        JsonObject evidence=view.deepCopy();
        if(evidence.has("snapshot")&&!evidence.get("snapshot").isJsonNull())evidence.getAsJsonObject("snapshot").remove("device");
        Files.write(new File(context.getFilesDir(),"subscription-runtime.json").toPath(),evidence.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }

    private String texts(AccessibilityNodeInfo node){
        if(node==null)return "";
        StringBuilder result=new StringBuilder();if(node.getText()!=null)result.append(node.getText()).append('\n');
        for(int index=0;index<node.getChildCount();index++)result.append(texts(node.getChild(index)));
        return result.toString();
    }

    private void screen()throws Exception{
        context.startActivity(SubscriptionUi.intent(context).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        String expected=arguments.getString("screen");assertNotNull(expected);
        String outcome=arguments.getString("outcome","current");
        String availability=SubscriptionUi.text(context).get(outcome.equals("offline")?"subscription_offline":"subscription_refresh_"+outcome);
        String rendered="";long deadline=android.os.SystemClock.elapsedRealtime()+30000;
        while(android.os.SystemClock.elapsedRealtime()<deadline){
            rendered=texts(InstrumentationRegistry.getInstrumentation().getUiAutomation().getRootInActiveWindow());
            if(rendered.contains(expected)&&rendered.contains(availability))break;
            Thread.sleep(200);
        }
        Files.write(new File(context.getFilesDir(),"subscription-screen.txt").toPath(),rendered.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertTrue("Expected subscription screen text: "+expected,rendered.contains(expected));
        assertTrue("Expected final refresh outcome",rendered.contains(availability));
        assertFalse(rendered.contains("Payment received"));assertFalse(rendered.contains("Оплата подтверждена"));
        JsonObject saved=worker(()->ChatRuntime.subscription(context,ChatRuntime.open(context,false)));
        java.util.Locale locale=AppLanguage.wrap(context).getResources().getConfiguration().getLocales().get(0);
        assertTrue(rendered.contains(SubscriptionPresentation.time(saved.get("confirmed_at").getAsLong(),locale,java.time.ZoneId.systemDefault())));
        if(!saved.get("snapshot").isJsonNull()){
            JsonObject snapshot=saved.getAsJsonObject("snapshot");
            String boundary=!snapshot.get("entitlement_until").isJsonNull()?"entitlement_until":!snapshot.get("grace_until").isJsonNull()?"grace_until":"paid_until";
            assertTrue(rendered.contains(SubscriptionPresentation.time(snapshot.get(boundary).getAsLong(),locale,java.time.ZoneId.systemDefault())));
        }
    }

    @Test public void enroll()throws Exception{
        worker(()->{new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+20000).activate(arguments.getString("invitation"));return null;});
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            context.getSharedPreferences("subscription-test",0).edit().putString("identity",identity.reference()).commit();
        }
        KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
        assertNull(keys.getKey("family-connect-friends-identity-v1",null).getEncoded());
    }

    @Test public void refreshOnly()throws Exception{refresh();}

    @Test public void inspectNatural()throws Exception{
        JsonObject view=worker(()->ChatRuntime.subscription(context,ChatRuntime.open(context,false)));
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            assertEquals(identity.reference(),view.getAsJsonObject("snapshot").get("device").getAsString());
        }
        verify(view);
        JsonObject notice=view.getAsJsonObject("notice");
        assertEquals(arguments.getString("read"),String.valueOf(notice.get("read").getAsBoolean()));
        assertEquals(arguments.getString("notified"),String.valueOf(notice.get("notified").getAsBoolean()));
    }

    private AccessibilityNodeInfo findText(AccessibilityNodeInfo node,String text){
        if(node==null)return null;
        if(node.isVisibleToUser()&&text.contentEquals(node.getText()==null?"":node.getText()))return node;
        for(int index=0;index<node.getChildCount();index++){
            AccessibilityNodeInfo found=findText(node.getChild(index),text);if(found!=null)return found;
        }
        return null;
    }

    private AccessibilityNodeInfo scrollable(AccessibilityNodeInfo node){
        if(node==null)return null;
        if(node.isScrollable())return node;
        for(int index=0;index<node.getChildCount();index++){
            AccessibilityNodeInfo found=scrollable(node.getChild(index));if(found!=null)return found;
        }
        return null;
    }

    @Test public void recoverThroughUi()throws Exception{
        context.startActivity(new Intent(context,FriendsActivity.class).putExtra("tab",3).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        AccessibilityNodeInfo button=null;long deadline=android.os.SystemClock.elapsedRealtime()+30000;
        while(button==null&&android.os.SystemClock.elapsedRealtime()<deadline){
            AccessibilityNodeInfo root=InstrumentationRegistry.getInstrumentation().getUiAutomation().getRootInActiveWindow();
            button=findText(root,"Get access");
            if(button==null){AccessibilityNodeInfo scroll=scrollable(root);if(scroll!=null)scroll.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD);}
            Thread.sleep(500);
        }
        assertNotNull(button);assertTrue(button.performAction(AccessibilityNodeInfo.ACTION_CLICK));
        var preferences=context.getSharedPreferences(FriendsActivity.class.getName(),Context.MODE_PRIVATE);
        while(!preferences.getBoolean("activated",false)&&android.os.SystemClock.elapsedRealtime()<deadline)Thread.sleep(200);
        assertTrue("Activation must come from real authenticated UI recovery",preferences.getBoolean("activated",false));
    }

    @Test public void refreshAndScreen()throws Exception{refresh();screen();}

    @Test public void offlineRestart()throws Exception{
        assertFalse(new ChatNetworkAndroid(context).available());
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            assertEquals(context.getSharedPreferences("subscription-test",0).getString("identity",null),identity.reference());
        }
        JsonObject cached=worker(()->ChatRuntime.subscription(context,ChatRuntime.open(context,false)));
        assertFalse(cached.has("refresh_status"));verify(cached);
        refresh();screen();
        KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
        assertNull(keys.getKey("family-connect-chat-store-v1",null).getEncoded());
    }

    private StatusBarNotification[] notices(){
        return java.util.Arrays.stream(context.getSystemService(NotificationManager.class).getActiveNotifications())
            .filter(notice->notice.getTag()!=null&&notice.getTag().startsWith("chat:subscription:")).toArray(StatusBarNotification[]::new);
    }

    @Test public void notifications()throws Exception{
        JsonObject fresh=refresh();
        worker(()->{ChatRuntime.deliverNotifications(context,ChatRuntime.open(context,false));return null;});
        boolean permitted=context.getSystemService(NotificationManager.class).areNotificationsEnabled();
        assertEquals(arguments.getString("permitted","true"),String.valueOf(permitted));
        assertEquals(permitted?1:0,notices().length);
        if(permitted){
            long posted=notices()[0].getPostTime();String tag=notices()[0].getTag();
            assertEquals("chat:subscription:"+fresh.getAsJsonObject("notice").get("id").getAsString(),tag);
            assertEquals(ChatNotifications.EVENTS,notices()[0].getNotification().getChannelId());
            refresh();worker(()->{ChatRuntime.deliverNotifications(context,ChatRuntime.open(context,false));return null;});
            assertEquals(1,notices().length);assertEquals(posted,notices()[0].getPostTime());
            context.getSharedPreferences("subscription-test",0).edit().putLong("posted",posted).putString("tag",tag).commit();
        }
    }

    @Test public void notificationRestart()throws Exception{
        int before=notices().length;
        assertTrue(refresh().getAsJsonObject("notice").get("notified").getAsBoolean());
        worker(()->{ChatRuntime.deliverNotifications(context,ChatRuntime.open(context,false));return null;});
        assertEquals(before,notices().length);
        if(before>0){
            assertEquals(context.getSharedPreferences("subscription-test",0).getLong("posted",0),notices()[0].getPostTime());
            assertEquals(context.getSharedPreferences("subscription-test",0).getString("tag",null),notices()[0].getTag());
        }
    }

    @Test public void screenOnly()throws Exception{screen();}

    @Test public void cancelledOwner()throws Exception{
        CompletableFuture<JsonObject> response=new CompletableFuture<>();
        var request=ChatRuntime.SUBSCRIPTION_REFRESH.begin();assertNotNull(request);request.cancel();
        ChatRuntime.refreshSubscription(context,request,response::complete);
        assertEquals("cancelled",response.get(10,TimeUnit.SECONDS).get("refresh_status").getAsString());
    }

    @Test public void cancelledLateResponse()throws Exception{
        JsonObject before=worker(()->ChatRuntime.subscription(context,ChatRuntime.open(context,false)));
        CompletableFuture<JsonObject> response=new CompletableFuture<>();
        var request=ChatRuntime.SUBSCRIPTION_REFRESH.begin();assertNotNull(request);
        ChatRuntime.refreshSubscription(context,request,response::complete);Thread.sleep(500);request.cancel();
        assertEquals("cancelled",response.get(10,TimeUnit.SECONDS).get("refresh_status").getAsString());
        assertEquals(before,worker(()->ChatRuntime.subscription(context,ChatRuntime.open(context,false))));
    }

    @Test public void tlsHostnameRejected()throws Exception{
        javax.net.ssl.HttpsURLConnection connection=(javax.net.ssl.HttpsURLConnection)new java.net.URL("https://localhost:18444/friends/device/subscription").openConnection();
        connection.setConnectTimeout(3000);connection.setReadTimeout(3000);
        try{assertThrows(javax.net.ssl.SSLPeerUnverifiedException.class,connection::getResponseCode);}
        finally{connection.disconnect();}
    }

    @Test public void networkPaths()throws Exception{
        var manager=context.getSystemService(android.net.ConnectivityManager.class);
        var observations=new com.google.gson.JsonArray();boolean reachable=false;
        for(var network:manager.getAllNetworks()){
            var caps=manager.getNetworkCapabilities(network);
            if(caps==null||!caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_NOT_VPN)||!caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET))continue;
            JsonObject result=new JsonObject();
            result.addProperty("transport",caps.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI)?"wifi":"cellular");
            javax.net.ssl.HttpsURLConnection connection=(javax.net.ssl.HttpsURLConnection)network.openConnection(new java.net.URL("https://10.0.2.2:18443/"));
            connection.setConnectTimeout(3000);connection.setReadTimeout(3000);
            try{int status=connection.getResponseCode();result.addProperty("status",status);reachable|=status==501;}
            catch(Exception failure){result.addProperty("failure",failure.getClass().getSimpleName());if(failure.getCause()!=null)result.addProperty("cause",failure.getCause().getClass().getSimpleName());}
            finally{connection.disconnect();}
            observations.add(result);
        }
        Files.write(new File(context.getFilesDir(),"subscription-network.json").toPath(),observations.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertTrue("Test TLS origin must be reachable on at least one underlay",reachable);
    }
}
