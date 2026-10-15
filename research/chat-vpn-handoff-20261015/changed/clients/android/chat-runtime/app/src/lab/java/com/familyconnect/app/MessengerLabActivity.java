package com.familyconnect.app;

import android.app.Activity;
import android.app.NotificationManager;
import android.os.Bundle;
import com.google.gson.*;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Base64;
import java.util.concurrent.TimeUnit;

public final class MessengerLabActivity extends Activity {
    private static boolean observing;
    private static String failure = "";
    private static final String ORIGIN = "http://10.0.2.2:38874";
    private static native String sharing(long handle,byte[] response,byte[] identity,byte[] anchor,String body,Object protector);

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        android.widget.TextView view = new android.widget.TextView(this);
        view.setText("LOCAL PION / messenger acceptance only. VPN remains OFF."); setContentView(view);
        action();
    }

    @Override protected void onNewIntent(android.content.Intent intent) {
        super.onNewIntent(intent); setIntent(intent); action();
    }

    private void action() {
        String mode = getIntent().getStringExtra("mode");
        String text = getIntent().getStringExtra("text");
        ChatRuntime.WORKER.execute(() -> {
            try {
                if ("prepare".equals(mode)) prepare();
                else {
                    ChatLocalAndroid chat = ChatRuntime.open(this, false);
                    if ("sharing".equals(mode)) checkSharing(chat);
                    if ("block-channel".equals(mode)) {
                        getSystemService(NotificationManager.class).createNotificationChannel(new android.app.NotificationChannel(ChatNotifications.MESSAGES,"Messages",NotificationManager.IMPORTANCE_NONE));
                    }
                    if ("reply".equals(mode)) {
                        JsonObject peer = JsonParser.parseString(read("lab-peer.json")).getAsJsonObject();
                        JsonObject request = new JsonObject(); request.addProperty("address", peer.get("address").getAsString());
                        request.addProperty("text", text); chat.call("queue", request);
                    }
                    runOnUiThread(() -> ChatDeliveryService.start(this));
                }
                if (!observing) {
                    observing = true;
                    ChatRuntime.WORKER.scheduleWithFixedDelay(this::observe, 0, 2, TimeUnit.SECONDS);
                }
            } catch (Exception | LinkageError error) { failure=error.toString(); observe(); }
        });
    }

    private JsonObject post(String path, JsonObject value) throws Exception {
        HttpURLConnection connection=(HttpURLConnection)new URL(ORIGIN+path).openConnection();
        connection.setConnectTimeout(5000);connection.setReadTimeout(20000);connection.setRequestMethod("POST");connection.setDoOutput(true);
        byte[] raw=value.toString().getBytes(StandardCharsets.UTF_8);connection.setFixedLengthStreamingMode(raw.length);
        try {try(OutputStream output=connection.getOutputStream()){output.write(raw);}
            if(connection.getResponseCode()!=200)throw new IOException("lab_setup_"+connection.getResponseCode());
            try(InputStream input=connection.getInputStream()){return JsonParser.parseString(new String(input.readAllBytes(),StandardCharsets.UTF_8)).getAsJsonObject();}
        } finally {connection.disconnect();}
    }

    private void pin(ChatLocalAndroid chat) throws Exception {
        try(InputStream input=getAssets().open("service-publisher.pub")) {
            chat.pinPublisher(new String(input.readAllBytes(),StandardCharsets.US_ASCII).trim());
        }
    }

    private void prepare() throws Exception {
        NativeRestricted.load();
        ChatLocalAndroid chat=ChatRuntime.open(this,true); pin(chat);
        try(ControlIdentity identity=new FriendsIdentityVault(this).create()) {
            JsonObject request=new JsonObject();request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));request.addProperty("wireguard_public_key",identity.wireguardPublicKey());
            JsonObject challenge=post("/lab/challenge",request);
            request=new JsonObject();request.add("proof",identity.proveTransportKey(challenge.get("challenge").getAsString()));
            challenge=post("/lab/activate",request);
            request=new JsonObject();request.add("proof",identity.proveTransportKey(challenge.get("challenge").getAsString()));
            request.addProperty("chat_public",chat.call("profile",new JsonObject()).getAsJsonObject().get("public").getAsString());
            JsonObject response=post("/lab/bootstrap",request);
            RestrictedCache cache=new RestrictedCache(new RestrictedVault(this),raw->NativeRestricted.validateDelivery(raw,identity.publicIdentity(),ControlTrust.anchor(this)));
            cache.accept(response.get("delivery").toString().getBytes(StandardCharsets.UTF_8));
            JsonObject contact=new JsonObject();contact.addProperty("public",response.get("peer").getAsString());
            JsonObject preview=chat.call("preview_contact",contact).getAsJsonObject();
            contact.add("fingerprint",preview.get("fingerprint"));chat.call("trust_contact",contact);
            write("lab-peer.json",preview.toString());
            write("lab-prepared.json",chat.call("profile",new JsonObject()).toString());
        }
    }

    private void observe() {
        JsonObject state=new JsonObject();state.addProperty("pid",android.os.Process.myPid());state.addProperty("time",System.currentTimeMillis());state.addProperty("failure",failure);state.addProperty("service",ChatDeliveryService.running);
        try {
            ChatLocalAndroid chat=ChatRuntime.open(this,false);
            for(String operation:new String[]{"profile","inbox","service_events","delivery_state"})state.add(operation,chat.call(operation,new JsonObject()));
            JsonObject peer=JsonParser.parseString(read("lab-peer.json")).getAsJsonObject();
            JsonObject request=new JsonObject();request.add("address",peer.get("address"));request.addProperty("offset",0);request.addProperty("limit",100);
            state.add("history",chat.call("history",request));
            JsonArray notifications=new JsonArray();
            for(var notification:getSystemService(NotificationManager.class).getActiveNotifications()) {
                JsonObject row=new JsonObject();row.addProperty("id",notification.getId());row.addProperty("tag",notification.getTag());row.addProperty("channel",notification.getNotification().getChannelId());notifications.add(row);
            }
            state.add("notifications",notifications);
            var channel=getSystemService(NotificationManager.class).getNotificationChannel(ChatNotifications.MESSAGES);
            if(channel!=null)state.addProperty("message_channel_importance",channel.getImportance());
            state.addProperty("notifications_enabled",getSystemService(NotificationManager.class).areNotificationsEnabled());
        } catch(Exception error) {state.addProperty("observation_error",error.toString());}
        try {write("lab-state.json",state.toString());}catch(Exception ignored){}
    }

    private String read(String name)throws Exception{return new String(Files.readAllBytes(new File(getFilesDir(),name).toPath()),StandardCharsets.UTF_8);}
    private void write(String name,String value)throws Exception{Files.write(new File(getFilesDir(),name).toPath(),value.getBytes(StandardCharsets.UTF_8));}

    private void checkSharing(ChatLocalAndroid chat)throws Exception {
        var carrierField=ChatRuntime.class.getDeclaredField("carrier");carrierField.setAccessible(true);
        var handleField=ChatCarrier.class.getDeclaredField("handle");handleField.setAccessible(true);
        long handle=handleField.getLong(carrierField.get(null));
        try(ControlIdentity identity=new FriendsIdentityVault(this).load()) {
            byte[] anchor=ControlTrust.anchor(this);
            RestrictedCache cache=new RestrictedCache(new RestrictedVault(this),raw->NativeRestricted.validateDelivery(raw,identity.publicIdentity(),anchor));
            byte[] response=cache.usable(),material=identity.material(),secret=java.util.Arrays.copyOf(material,64);
            JsonObject body=new JsonObject();body.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));body.addProperty("wireguard_public_key",identity.wireguardPublicKey());
            body.addProperty("chat_public",chat.call("profile",new JsonObject()).getAsJsonObject().get("public").getAsString());
            try{write("lab-sharing.json",sharing(handle,response,secret,anchor,body.toString(),new ChatNetworkAndroid(this)));}
            finally{java.util.Arrays.fill(material,(byte)0);java.util.Arrays.fill(secret,(byte)0);java.util.Arrays.fill(response,(byte)0);}
        }
    }
}
