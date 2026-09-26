package com.familyconnect.app;

import android.app.*;
import android.content.*;
import android.os.Build;
import android.content.pm.PackageManager;
import com.google.gson.JsonObject;

final class ChatNotifications {
    static final String MESSAGES="chat-messages-v1",EVENTS="service-events-v1",DELIVERY="chat-delivery-v1";
    static void channels(Context c){
        NotificationManager manager=c.getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel(MESSAGES,c.getString(R.string.chat_notifications),NotificationManager.IMPORTANCE_HIGH));
        manager.createNotificationChannel(new NotificationChannel(EVENTS,c.getString(R.string.service_events),NotificationManager.IMPORTANCE_DEFAULT));
        manager.createNotificationChannel(new NotificationChannel(DELIVERY,c.getString(R.string.chat_background),NotificationManager.IMPORTANCE_LOW));
    }
    static PendingIntent open(Context c,String peer){
        Intent intent=new Intent(c,ChatActivity.class).setAction("chat:"+peer).putExtra("chat_peer",peer).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
        return PendingIntent.getActivity(c,0,intent,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
    }
    static Notification ongoing(Context c){
        channels(c);
        Notification.Builder builder=new Notification.Builder(c,DELIVERY).setSmallIcon(R.drawable.ic_shield).setContentTitle(c.getString(R.string.chat_background)).setContentText(c.getString(R.string.chat_background_hint)).setContentIntent(open(c,"")).setOngoing(true).setShowWhen(false);
        if(Build.VERSION.SDK_INT>=31)builder.setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE);
        return builder.build();
    }
    static boolean message(Context c,String peer,JsonObject message,boolean service,String name){
        channels(c);NotificationManager manager=c.getSystemService(NotificationManager.class);
        if(!manager.areNotificationsEnabled())return false;
        String channel=service?EVENTS:MESSAGES;
        if(manager.getNotificationChannel(channel).getImportance()==NotificationManager.IMPORTANCE_NONE)return false;
        String title=service?"Family Connect":name!=null?name:c.getString(R.string.chat_contact)+" "+peer.substring(0,8);
        String text=service?message.get("title").getAsString():c.getString(R.string.chat_new_message);
        Notification publicView=new Notification.Builder(c,channel).setSmallIcon(R.drawable.ic_shield).setContentTitle("Family Connect").setContentText(c.getString(R.string.chat_new_message)).build();
        Notification notification=new Notification.Builder(c,channel).setSmallIcon(R.drawable.ic_shield).setContentTitle(title).setContentText(text).setCategory(Notification.CATEGORY_MESSAGE).setVisibility(Notification.VISIBILITY_PRIVATE).setPublicVersion(publicView).setContentIntent(open(c,peer)).setAutoCancel(true).setNumber(message.has("unread")?message.get("unread").getAsInt():1).build();
        try{manager.notify("chat:"+peer,100,notification);return true;}catch(SecurityException denied){return false;}
    }
    static void cancel(Context c,String peer){c.getSystemService(NotificationManager.class).cancel("chat:"+peer,100);}
    static void request(Activity activity){
        channels(activity);
        if(Build.VERSION.SDK_INT>=33&&activity.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED){
            var prefs=activity.getSharedPreferences("chat-notifications",Context.MODE_PRIVATE);
            if(!prefs.getBoolean("permission_requested",false)){prefs.edit().putBoolean("permission_requested",true).apply();activity.requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS},73);}
        }
    }
}
