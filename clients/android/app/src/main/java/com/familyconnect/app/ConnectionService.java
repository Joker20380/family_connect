package com.familyconnect.app;
import android.app.*;
import android.content.Intent;
import android.net.VpnService;
import android.os.*;
import java.util.concurrent.*;

public final class ConnectionService extends Service {
    static volatile String status="off",activeTransport="wg",requestedTransport="wg";
    static volatile boolean failed=false;
    static volatile String healthStatus="off",vpnSource=null;
    static volatile long sessionId=0;
    static volatile String controlOutcome;
    static volatile long controlResultId;
    private static final java.util.concurrent.atomic.AtomicLong sessionCounter=new java.util.concurrent.atomic.AtomicLong();
    private final Object operationOwner=new Object();
    private TunnelEngine engine;
    private final ScheduledExecutorService rnsWorker=Executors.newSingleThreadScheduledExecutor();
    private volatile ControlRnsAndroid rnsCarrier;
    private volatile boolean rnsEnabled;

    private volatile Thread workerThread;
    private final ScheduledExecutorService worker=Executors.newSingleThreadScheduledExecutor(task->{
        Thread thread=new Thread(task,"fc-vpn-worker");workerThread=thread;return thread;
    });
    private volatile ControlTrafficHealth controlHealth;
    private boolean controlApplying;
    private volatile long managedExpiry;
    private volatile Runnable leaseTask;
    private final Handler main=new Handler(Looper.getMainLooper());
    private volatile boolean stopping=false,closing=false,claimed=false;
    private volatile long generation=0;
    private boolean started=false,automatic=false;
    private final AutoPolicy policy=new AutoPolicy();
    private volatile VpnHealth health;
    private ScheduledFuture<?> pending;
    private String source;
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        startForeground(1,notification());
        if(intent!=null&&"disconnect".equals(intent.getAction())){if(!started){stopSelf();return START_NOT_STICKY;}cancel();worker.execute(()->owned(this::stopConnection));return START_NOT_STICKY;}
        final boolean sync=intent!=null&&"sync-control".equals(intent.getAction());
        final boolean intake=intent!=null&&"apply-control".equals(intent.getAction());
        if(started||stopping||closing){if(intake||sync)reportControl("BUSY");return START_NOT_STICKY;}
        final String priorStatus=status;
        byte[] received=null;
        if(intake){try{received=ControlIntake.copy(intent.getByteArrayExtra("envelope"));}
            catch(Exception invalid){reportControl("FAILED");stopSelf();return START_NOT_STICKY;}}
        final byte[] incoming=received;
        started=true;status="connecting";failed=false;
        String id=intent==null?"wg":intent.getStringExtra("transport");requestedTransport=id==null?"wg":id;
        automatic="auto".equals(requestedTransport);
        final boolean connectRequested=intent!=null&&"connect".equals(intent.getAction());
        worker.execute(()->{
            try{ControlOperations.APP.claim(operationOwner);claimed=true;}
            catch(Exception busy){if(intake)reportControl("BUSY");main.post(()->{status=priorStatus;stopSelf();});return;}
            owned(()->{
                try{
                    if(sync){
                        try(ControlIdentity identity=new ControlIdentityVault(this).load()){
                            com.google.gson.JsonObject enrolled=new ControlEnrollmentAndroid(this).read();
                            if(!"ENROLLED".equals(ControlJson.text(enrolled.get("phase")))||!identity.reference().equals(ControlJson.text(enrolled.get("device"))))
                                throw new java.io.IOException("Enrollment required");
                        }
                        if("FAILED".equals(controlNow(null,true)))return;
                        if(!stopping&&!closing){rnsEnabled=true;rnsWorker.execute(this::syncControl);}
                    } else if(intake){
                        if(stopping||closing)throw new java.io.IOException("Control intake cancelled");
                        reportControl(controlNow(ControlIntake.copy(incoming),false));
                    } else ControlStartup.run(connectRequested,()->ControlMutationGate.managed(this),
                        ()->controlNow(null,true),()->controlNow(null,true,true),
                        ()->{if(automatic)next();else start(Transport.parse(requestedTransport));});
                    if(engine==null&&!rnsEnabled&&!stopping&&!closing)stopConnection();
                }
                catch(Exception|LinkageError e){if(intake||sync)reportControl("FAILED");failed=true;cancel();stopConnection();}
            });
        });
        return START_NOT_STICKY;
    }
    private void syncControl(){
        if(!rnsEnabled||stopping||closing)return;
        ControlRnsAndroid transport=new ControlRnsAndroid(this);rnsCarrier=transport;
        try(ControlIdentity identity=new ControlIdentityVault(this).load()){
            transport.open();ControlCarrier carrier=new ControlCarrier(transport,identity,()->System.currentTimeMillis()/1000);
            ControlTransaction core=new ControlTransaction(controlJournal(identity),application(identity),()->System.currentTimeMillis()/1000,operationOwner);
            // flush() releases its journal monitor around each network request.
            core.flush(carrier);
            if(stopping||closing)return;
            byte[] raw=carrier.receive();
            if(stopping||closing)return;
            String result=control(raw,false).get();reportControl(result);
            if(!stopping&&!closing)core.flush(carrier);
        }catch(Exception|LinkageError unavailable){
            if(!stopping&&!closing)reportControl("UNAVAILABLE"); // Carrier outage must not stop a working VPN.
        }finally{
            try{transport.close();}catch(Exception|LinkageError ignored){}
            rnsCarrier=null;
            if(rnsEnabled&&!stopping&&!closing){try{rnsWorker.schedule(this::syncControl,60,TimeUnit.SECONDS);}catch(RejectedExecutionException closed){}}
        }
    }
    private ControlJournal controlJournal(ControlIdentity identity)throws Exception{
        String version=getPackageManager().getPackageInfo(getPackageName(),0).versionName;
        if(version==null)throw new java.io.IOException("Missing application version");
        version=version.split("-",2)[0];ControlProtocol.version(version);
        return new ControlJournal(new ControlJournalVault(this),identity,ControlTrust.anchor(this),version);
    }
    private static synchronized void reportControl(String result){controlOutcome=result;++controlResultId;}
    private void owned(Runnable action){
        try{ControlOperations.APP.session(operationOwner,action);}
        catch(ControlOperations.Stale ignored){/* Late callback belongs to a released service. */}
    }
    private void cancel(){rnsEnabled=false;ControlRnsAndroid transport=rnsCarrier;if(transport!=null)transport.cancel();stopping=true;status="connecting";healthStatus="off";VpnHealth h=health;if(h!=null)h.cancel();ControlTrafficHealth c=controlHealth;if(c!=null)c.cancel();}
    private void schedule(Runnable action,int seconds){if(!stopping&&!closing)pending=worker.schedule(()->owned(action),seconds,TimeUnit.SECONDS);}
    private boolean cleanup(){
        managedExpiry=0;Runnable lease=leaseTask;if(lease!=null){main.removeCallbacks(lease);leaseTask=null;}ControlTrafficHealth c=controlHealth;if(c!=null)c.cancel();
        ++generation;sessionId=sessionCounter.incrementAndGet();vpnSource=null;healthStatus="off";if(pending!=null)pending.cancel(false);if(health!=null){health.cancel();health=null;}
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
        source=type==Transport.TCP?"10.79.0.2":org.amnezia.awg.config.Config.parse(new java.io.ByteArrayInputStream(profile.getBytes(java.nio.charset.StandardCharsets.UTF_8))).getInterface().getAddresses().stream().filter(a->a.getAddress() instanceof java.net.Inet4Address).findFirst().orElseThrow(()->new IllegalArgumentException("IPv4 required")).getAddress().getHostAddress();
        final long token=++generation;sessionId=sessionCounter.incrementAndGet();vpnSource=source;healthStatus="checking";
        engine=TunnelEngine.create(this,type,up->{if(!up&&token==generation&&!stopping&&!closing){cancel();worker.execute(()->owned(this::stopConnection));}});
        engine.up(profile);
        if(stopping||closing){stopConnection();return;}
        health=new VpnHealth(this);if(!controlApplying)schedule(()->probe(token),1);
        if(!automatic&&!controlApplying){status="on";main.post(this::notifyState);}
    }
    private void probe(long token){
        if(token!=generation||stopping||closing)return;
        if(managedExpiry>0&&System.currentTimeMillis()/1000>=managedExpiry){cancel();stopConnection();return;}
        boolean good=health.check(source);
        if(token!=generation||stopping||closing)return;
        healthStatus=good?"ok":"unavailable";
        if(automatic&&policy.advance(good)){next();return;}
        if(good||!automatic)status="on";
        main.post(this::notifyState);
        schedule(()->probe(token),good?15:automatic?1:5);
    }
    private void armLease(long expiry){
        Runnable previous=leaseTask;if(previous!=null)main.removeCallbacks(previous);
        leaseTask=null;if(expiry==0)return;final long token=generation;
        Runnable expire=()->{
            if(token!=generation||managedExpiry!=expiry||stopping||closing)return;
            cancel();try{worker.execute(()->owned(this::stopConnection));}catch(RejectedExecutionException closed){}
        };
        leaseTask=expire;main.postDelayed(expire,Math.max(0,expiry-System.currentTimeMillis()/1000)*1000);
    }
    private void controlWorker(){
        if(Thread.currentThread()!=workerThread)throw new IllegalStateException("Control requires service worker");
        ControlOperations.APP.requireOwner(operationOwner);
    }
    private ControlApplication application(ControlIdentity identity){
        return new ControlApplication(new ControlApplication.Host(){
            public com.google.gson.JsonObject capture()throws Exception{
                controlWorker();com.google.gson.JsonObject saved=new com.google.gson.JsonObject(),profiles=new com.google.gson.JsonObject();
                for(Transport type:Transport.values()){
                    ProfileStore store=new ProfileStore(ConnectionService.this,type);
                    profiles.addProperty(type.id,store.present()?store.load():null);
                }
                saved.addProperty("schema",1);saved.add("profiles",profiles);
                saved.addProperty("active",engine==null?null:activeTransport);saved.addProperty("lease",engine==null?0:managedExpiry);return saved;
            }
            public void validate(String transport,String profile)throws Exception{
                controlWorker();Transport type=Transport.parse(transport);ProfileValidator.validate(profile,type);
                if(type!=Transport.TCP)org.amnezia.awg.config.Config.parse(new java.io.ByteArrayInputStream(profile.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            }
            public void stop()throws Exception{controlWorker();if(!cleanup())throw new java.io.IOException("VPN cleanup failed");}
            public void save(String transport,String profile)throws Exception{
                controlWorker();new ProfileStore(ConnectionService.this,Transport.parse(transport)).restoreOwned(operationOwner,profile);
            }
            public void start(String transport,long expiry)throws Exception{
                controlWorker();if(cancelled()||(expiry>0&&System.currentTimeMillis()/1000>=expiry))throw new java.io.IOException("Control start no longer permitted");
                automatic=false;requestedTransport=transport;ConnectionService.this.start(Transport.parse(transport));managedExpiry=expiry;armLease(expiry);
                if(cancelled()||engine==null)throw new java.io.IOException("Control start interrupted");
            }
            public boolean healthy(){
                controlWorker();ControlTrafficHealth check=new ControlTrafficHealth(ConnectionService.this);controlHealth=check;
                try{return !cancelled()&&check.check(source)&&!cancelled();}finally{check.cancel();controlHealth=null;}
            }
            public boolean cancelled(){return stopping||closing||VpnService.prepare(ConnectionService.this)!=null;}
        },identity);
    }
    /** Internal dispatch only. Trust comes from the packaged offline anchor, never an Intent.
     * Service startup supports explicit local signed-file intake. Network carrier remains separate.
     */
    CompletableFuture<String> control(byte[] envelope,boolean recoveryOnly){
        CompletableFuture<String> result=new CompletableFuture<>();
        if(!recoveryOnly&&(envelope==null||envelope.length>65536)){
            result.completeExceptionally(new IllegalArgumentException("Invalid control input"));return result;
        }
        final byte[] raw=envelope==null?null:envelope.clone();
        try{worker.execute(()->{
            try{ControlOperations.APP.session(operationOwner,()->{
                try{result.complete(controlNow(raw,recoveryOnly));}
                catch(Exception|LinkageError failure){failed=true;cancel();stopConnection();result.completeExceptionally(failure);}
            });}catch(ControlOperations.Stale stale){result.completeExceptionally(stale);}
        });}catch(RejectedExecutionException closed){result.completeExceptionally(closed);}
        return result;
    }
    private String controlNow(byte[] raw,boolean recoveryOnly)throws Exception{
        return controlNow(raw,recoveryOnly,false);
    }
    private String controlNow(byte[] raw,boolean recoveryOnly,boolean resume)throws Exception{
        controlWorker();
        controlApplying=true;if(pending!=null)pending.cancel(false);
        try(ControlIdentity identity=new ControlIdentityVault(this).load()){
            ControlJournal journal=controlJournal(identity);
            ControlTransaction core=new ControlTransaction(journal,application(identity),()->System.currentTimeMillis()/1000,operationOwner);
            String outcome;
            if(resume)outcome=core.resume();
            else if(recoveryOnly)outcome=core.recover();
            else outcome=ControlIntake.apply(core,identity,new ControlEnrollmentAndroid(this).read(),raw,()->engine!=null);
            if(outcome.equals("FAILED")){failed=true;cancel();stopConnection();}
            return outcome;
        }
        finally{
            controlApplying=false;
            if(engine!=null&&!stopping&&!closing){status="on";long token=generation;schedule(()->probe(token),1);main.post(this::notifyState);}
        }
    }
    private void stopConnection(){if(cleanup())main.post(()->{if(!closing)stopSelf();});}
    private Notification notification(){
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("vpn",getString(R.string.notification),NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,ConnectionService.class).setAction("disconnect"),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"vpn").setSmallIcon(R.drawable.ic_shield).setContentTitle(getString(R.string.notification))
            .setContentText((automatic?"AUTO · ":"")+activeTransport.toUpperCase(java.util.Locale.ROOT)+" · "+getString(status.equals("on")?(healthStatus.equals("unavailable")?R.string.health_unavailable:R.string.on):R.string.connecting)).setContentIntent(open)
            .setOngoing(true).addAction(new Notification.Action.Builder(null,getString(R.string.disconnect),stop).build()).build();
    }
    private void notifyState(){if(!closing)getSystemService(NotificationManager.class).notify(1,notification());}
    @Override public void onDestroy(){
        closing=true;rnsEnabled=false;ControlRnsAndroid transport=rnsCarrier;if(transport!=null)transport.cancel();rnsWorker.shutdownNow();if(claimed)cancel();else stopping=true;worker.execute(()->owned(()->{if(cleanup()){ControlOperations.APP.release(operationOwner);claimed=false;status="off";}}));worker.shutdown();stopForeground(STOP_FOREGROUND_REMOVE);super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
