package com.familyconnect.app;
import android.app.*;
import android.content.Intent;
import android.os.*;
import java.util.concurrent.*;

public final class ConnectionService extends Service {
    static volatile String status="off",activeTransport="wg";
    static volatile boolean failed=false;
    private TunnelEngine engine;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile boolean stopping=false,closing=false;
    private boolean started=false;
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        boolean down=intent!=null&&"disconnect".equals(intent.getAction());
        startForeground(1,notification());
        if(down){stopping=true;status="connecting";worker.execute(this::stopConnection);return START_NOT_STICKY;}
        if(started||stopping||closing)return START_NOT_STICKY;
        started=true;status="connecting";failed=false;
        String id=intent==null?"wg":intent.getStringExtra("transport");
        try{activeTransport=Transport.parse(id==null?"wg":id).id;notifyState();}catch(IllegalArgumentException ignored){}
        worker.execute(()->{
            try{
                Transport transport=Transport.parse(id==null?"wg":id);activeTransport=transport.id;
                String profile=ProfileValidator.validate(new ProfileStore(this,transport).load(),transport);
                if(stopping||closing){stopConnection();return;}
                engine=TunnelEngine.create(this,transport,up->main.post(()->{
                    if(up){if(!stopping&&!closing){status="on";notifyState();}}
                    else if(!stopping&&!closing){stopping=true;status="connecting";worker.execute(this::stopConnection);}
                }));
                engine.up(profile);
                if(stopping||closing)stopConnection();
            }catch(Exception|LinkageError e){failed=true;stopping=true;stopConnection();}
        });
        return START_NOT_STICKY;
    }
    private void stopConnection(){
        try{if(engine!=null)engine.down();}catch(Exception|LinkageError e){failed=true;status="cleanup-required";main.post(this::notifyState);return;}
        main.post(()->{if(!closing)stopSelf();});
    }
    private Notification notification(){
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("vpn",getString(R.string.notification),NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,ConnectionService.class).setAction("disconnect"),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"vpn").setSmallIcon(R.drawable.ic_shield).setContentTitle(getString(R.string.notification))
            .setContentText(activeTransport.toUpperCase(java.util.Locale.ROOT)+" · "+getString(status.equals("on")?R.string.on:R.string.connecting)).setContentIntent(open)
            .setOngoing(true).addAction(new Notification.Action.Builder(null,getString(R.string.disconnect),stop).build()).build();
    }
    private void notifyState(){getSystemService(NotificationManager.class).notify(1,notification());}
    @Override public void onDestroy(){
        closing=true;stopping=true;
        worker.execute(()->{try{if(engine!=null)engine.down();}catch(Exception|LinkageError e){failed=true;status="cleanup-required";return;}status="off";});
        worker.shutdown();stopForeground(STOP_FOREGROUND_REMOVE);super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
