package com.familyconnect.app;
import android.app.*;
import android.content.Intent;
import android.net.VpnService;
import android.os.*;
import java.util.concurrent.*;

public final class ConnectionService extends Service {
    static volatile String status="off",activeTransport="wg",requestedTransport="wg";
    static volatile boolean failed=false;
    private TunnelEngine engine;
    private final ScheduledExecutorService worker=Executors.newSingleThreadScheduledExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile boolean stopping=false,closing=false;
    private volatile long generation=0;
    private boolean started=false,automatic=false;
    private final AutoPolicy policy=new AutoPolicy();
    private volatile VpnHealth health;
    private ScheduledFuture<?> pending;
    private String source;
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        startForeground(1,notification());
        if(intent!=null&&"disconnect".equals(intent.getAction())){cancel();worker.execute(this::stopConnection);return START_NOT_STICKY;}
        if(started||stopping||closing)return START_NOT_STICKY;
        started=true;status="connecting";failed=false;
        String id=intent==null?"wg":intent.getStringExtra("transport");requestedTransport=id==null?"wg":id;
        automatic="auto".equals(requestedTransport);
        worker.execute(()->{if(automatic)next();else try{start(Transport.parse(requestedTransport));}catch(Exception|LinkageError e){failed=true;cancel();stopConnection();}});
        return START_NOT_STICKY;
    }
    private void cancel(){stopping=true;status="connecting";VpnHealth h=health;if(h!=null)h.cancel();}
    private void schedule(Runnable action,int seconds){if(!stopping&&!closing)pending=worker.schedule(action,seconds,TimeUnit.SECONDS);}
    private boolean cleanup(){
        ++generation;if(pending!=null)pending.cancel(false);if(health!=null){health.cancel();health=null;}
        try{if(engine!=null){engine.down();engine=null;}return true;}
        catch(Exception|LinkageError e){failed=true;stopping=true;status="cleanup-required";main.post(this::notifyState);return false;}
    }
    private void next(){
        status="connecting";
        if(!cleanup())return;
        if(stopping||closing){stopConnection();return;}
        // Revocation is terminal: never open a permission dialog or another tunnel automatically.
        if(VpnService.prepare(this)!=null){cancel();stopConnection();return;}
        Transport candidate;
        while((candidate=policy.next())!=null){
            if(!new ProfileStore(this,candidate).exists())continue;
            try{start(candidate);return;}catch(Exception|LinkageError e){if(!cleanup())return;if(stopping||closing){stopConnection();return;}}
        }
        failed=true;cancel();stopConnection();
    }
    private void start(Transport type)throws Exception{
        String profile=ProfileValidator.validate(new ProfileStore(this,type).load(),type);
        if(stopping||closing){stopConnection();return;}
        activeTransport=type.id;status="connecting";main.post(this::notifyState);
        if(automatic)source=type==Transport.TCP?"10.79.0.2":org.amnezia.awg.config.Config.parse(new java.io.ByteArrayInputStream(profile.getBytes(java.nio.charset.StandardCharsets.UTF_8))).getInterface().getAddresses().stream().filter(a->a.getAddress() instanceof java.net.Inet4Address).findFirst().orElseThrow(()->new IllegalArgumentException("IPv4 required")).getAddress().getHostAddress();
        final long token=++generation;
        engine=TunnelEngine.create(this,type,up->{if(!up&&token==generation&&!stopping&&!closing){cancel();worker.execute(this::stopConnection);}});
        engine.up(profile);
        if(stopping||closing){stopConnection();return;}
        if(automatic){health=new VpnHealth(this);schedule(()->probe(token),1);}
        else{status="on";main.post(this::notifyState);}
    }
    private void probe(long token){
        if(token!=generation||stopping||closing)return;
        boolean good=health.check(source);
        if(token!=generation||stopping||closing)return;
        if(policy.advance(good)){next();return;}
        if(good){status="on";main.post(this::notifyState);}
        schedule(()->probe(token),good?15:1);
    }
    private void stopConnection(){if(cleanup())main.post(()->{if(!closing)stopSelf();});}
    private Notification notification(){
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("vpn",getString(R.string.notification),NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,ConnectionService.class).setAction("disconnect"),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"vpn").setSmallIcon(R.drawable.ic_shield).setContentTitle(getString(R.string.notification))
            .setContentText((automatic?"AUTO · ":"")+activeTransport.toUpperCase(java.util.Locale.ROOT)+" · "+getString(status.equals("on")?R.string.on:R.string.connecting)).setContentIntent(open)
            .setOngoing(true).addAction(new Notification.Action.Builder(null,getString(R.string.disconnect),stop).build()).build();
    }
    private void notifyState(){if(!closing)getSystemService(NotificationManager.class).notify(1,notification());}
    @Override public void onDestroy(){
        closing=true;cancel();worker.execute(()->{if(cleanup())status="off";});worker.shutdown();stopForeground(STOP_FOREGROUND_REMOVE);super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
