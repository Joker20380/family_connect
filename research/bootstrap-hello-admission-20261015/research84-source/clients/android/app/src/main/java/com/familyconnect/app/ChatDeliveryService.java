package com.familyconnect.app;

import android.app.Service;
import android.content.*;
import android.os.IBinder;

/** User-visible, independent encrypted mailbox delivery while the UI is closed. */
public final class ChatDeliveryService extends Service {
    static volatile String startFailure="";
    static volatile boolean running;
    static boolean enabled(Context context){return context.getSharedPreferences("chat-notifications",Context.MODE_PRIVATE).getBoolean("background",true);}
    static void start(Context context){
        if(!context.getPackageName().endsWith(".friends")||!enabled(context))return;
        try{context.startForegroundService(new Intent(context,ChatDeliveryService.class));startFailure="";}catch(IllegalStateException|SecurityException error){startFailure=error.getClass().getSimpleName();}
    }
    @Override public void onCreate(){super.onCreate();running=true;startForeground(42,ChatNotifications.ongoing(this));ChatRuntime.start(this);}
    @Override public int onStartCommand(Intent intent,int flags,int startId){return START_STICKY;}
    @Override public IBinder onBind(Intent intent){return null;}
    @Override public void onDestroy(){running=false;ChatRuntime.stop();super.onDestroy();}
}
