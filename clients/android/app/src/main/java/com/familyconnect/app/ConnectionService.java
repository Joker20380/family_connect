package com.familyconnect.app;

import android.app.*;
import android.content.Intent;
import android.os.*;
import com.wireguard.android.backend.GoBackend;
import com.wireguard.android.backend.Tunnel;
import com.wireguard.config.Config;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

public final class ConnectionService extends Service {
    static volatile String status="off";
    static volatile boolean failed=false;
    private GoBackend backend;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile boolean closing=false;
    private final Tunnel tunnel=new Tunnel() {
        public String getName(){return "fc-android";}
        public void onStateChange(State state) {
            status=state==State.UP?"on":"off";
            main.post(()->{if(!closing){if(state==State.UP)notifyState();else stopSelf();}});
        }
    };
    @Override public void onCreate(){super.onCreate();backend=new GoBackend(this);}
    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        boolean down=intent!=null&&"disconnect".equals(intent.getAction());
        status=down?status:"connecting";failed=false;
        startForeground(1,notification());
        worker.execute(()->{
            try {
                if(down){backend.setState(tunnel,Tunnel.State.DOWN,null);status="off";main.post(this::stopSelf);return;}
                String profile=new ProfileStore(this).load();
                Config config=Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8)));
                if(closing)return;
                backend.setState(tunnel,Tunnel.State.UP,config);
                if(closing)backend.setState(tunnel,Tunnel.State.DOWN,null);
            } catch(Exception e){failed=true;status="off";main.post(this::stopSelf);}
        });
        return START_NOT_STICKY;
    }
    private Notification notification() {
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("vpn",getString(R.string.notification),NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,ConnectionService.class).setAction("disconnect"),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"vpn").setSmallIcon(R.drawable.ic_shield).setContentTitle(getString(R.string.notification))
            .setContentText(getString(status.equals("on")?R.string.on:R.string.connecting)).setContentIntent(open)
            .setOngoing(true).addAction(new Notification.Action.Builder(null,getString(R.string.disconnect),stop).build()).build();
    }
    private void notifyState(){getSystemService(NotificationManager.class).notify(1,notification());}
    @Override public void onDestroy() {
        closing=true;
        worker.execute(()->{try{backend.setState(tunnel,Tunnel.State.DOWN,null);}catch(Exception ignored){}status="off";});
        worker.shutdown();stopForeground(STOP_FOREGROUND_REMOVE);super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
