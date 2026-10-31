package com.familyconnect.app;

import android.content.Context;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

final class FriendsRestricted {
    private static final class Selection {
        final boolean attempted;
        private final byte[] response;
        private final boolean availabilityFailure;
        Selection(boolean attempted,byte[] response,boolean availabilityFailure){this.attempted=attempted;this.response=response==null?null:response.clone();this.availabilityFailure=availabilityFailure;}
        byte[] copy(boolean restoring)throws ConnectivityOrchestrator.Rejected{return RestrictedBootstrap.select(response,availabilityFailure,restoring);}
    }
    private static CompletableFuture<Selection> running;
    private static final AtomicBoolean reconciled=new AtomicBoolean();
    static volatile String refresh="NOT_ATTEMPTED";
    static volatile boolean denied;
    private static volatile OwnerPrewarmReceipt observation;
    static RestrictedCache cache(Context context,ControlIdentity identity)throws Exception{
        byte[] publicIdentity=identity.publicIdentity(),anchor=ControlTrust.anchor(context);
        return RestrictedCache.detailed(new RestrictedVault(context),raw->{NativeRestricted.load();int code=NativeRestricted.validationCode(raw,publicIdentity,anchor);return code==0?ReadinessImportResult.Code.READY:code==2?ReadinessImportResult.Code.BOOTSTRAP_VALIDATION_FAILED:ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED;});
    }
    static byte[] ready(Context context,ControlIdentity identity,long deadline,java.util.function.BooleanSupplier cancelled)throws Exception{
        return ready(context,identity,deadline,cancelled,false);
    }
    static byte[] ready(Context context,ControlIdentity identity,long deadline,java.util.function.BooleanSupplier cancelled,boolean restoring)throws Exception{
        check(deadline,cancelled);
        Selection selected=await(start(context,true),deadline,cancelled);
        check(deadline,cancelled);
        if(!selected.attempted){
            selected=await(start(context,true),deadline,cancelled);
            check(deadline,cancelled);
        }
        return selected.copy(restoring);
    }
    private static void check(long deadline,java.util.function.BooleanSupplier cancelled)throws ConnectivityOrchestrator.Rejected{
        if(denied)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.AUTH);
        if(cancelled.getAsBoolean())throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.CANCELLED);
        if(android.os.SystemClock.elapsedRealtime()>=deadline)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.NETWORK);
    }
    private static Selection await(CompletableFuture<Selection> pending,long deadline,java.util.function.BooleanSupplier cancelled)throws Exception{
        while(true){
            check(deadline,cancelled);
            try{return pending.get(Math.min(100,Math.max(1,deadline-android.os.SystemClock.elapsedRealtime())),TimeUnit.MILLISECONDS);}
            catch(TimeoutException waiting){}
        }
    }
    static void prewarm(Context source){
        if(source.getPackageName().equals("com.familyconnect.app.friends"))start(source,false);
    }
    private static synchronized CompletableFuture<Selection> start(Context source,boolean required){
        if(running!=null&&!running.isDone())return running;
        CompletableFuture<Selection> pending=new CompletableFuture<>();running=pending;
        Context context=source.getApplicationContext();
        String startedConnection=Diagnostics.readinessConnection(context);
        new Thread(()->{
            boolean attempted=false;
            boolean availabilityFailure=false;
            byte[] selected=null;
            OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
            ReadinessFetchTrace trace=new ReadinessFetchTrace(receipt,startedConnection,System.currentTimeMillis());
            ReadinessProduct product=null;
            try(ProvisioningTestGate.Permit permit=ProvisioningTestGate.enter(context);
                    ControlIdentity identity=new FriendsIdentityVault(context).load()){
                RestrictedCache cache=cache(context,identity);
                product=new ReadinessProduct(cache,new ReadinessReceiptStore(context),BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE);
                if(!permit.blocked()&&reconciled.compareAndSet(false,true)){
                    ReadinessImportResult restored;OwnerPrewarmReceipt previous;
                    synchronized(RestrictedVault.LOCK){restored=product.restart(System.currentTimeMillis()/1000);previous=cache.context();}
                    Diagnostics.readinessResult(context,restored.code());
                    if(previous==null)product.record(restored);
                    else product.publish(restored,payload->new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+15000).readinessAck(identity,payload));
                }
                if(!permit.blocked())synchronized(RestrictedVault.LOCK){if(!cache.attempt(System.currentTimeMillis()/1000,required))return;}
                attempted=true;
                refresh="IN_PROGRESS";
                observation=receipt;ReadinessImportResult result;
                RestrictedBootstrap.Selection startup=RestrictedBootstrap.refresh(cache,product,receipt,
                    ()->{permit.requireAvailable();return new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+30000,trace).restrictedReadiness(identity,receipt);},
                    RestrictedVault.LOCK,()->System.currentTimeMillis()/1000);
                result=startup.result;selected=startup.response;refresh=startup.status;
                synchronized(RestrictedVault.LOCK){trace.cache(cache.diagnostic(System.currentTimeMillis()/1000));}
                trace.complete(result.code(),selected!=null,refresh.equals("SUCCESS"),System.currentTimeMillis());
                Diagnostics.readinessFetch(context,trace);
                availabilityFailure=startup.availabilityFailure;
                if(startup.authorizationRejected)denied=true;
                else if(result.code()==ReadinessImportResult.Code.READY)denied=false;
                Diagnostics.readinessResult(context,result.code());
                if(permit.blocked())product.record(result);
                else product.publish(result,payload->new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+15000).readinessAck(identity,payload));
            }catch(Exception | LinkageError failure){availabilityFailure=false;if(selected!=null){Arrays.fill(selected,(byte)0);selected=null;}refresh="UNAVAILABLE";
                trace.failed(failure);trace.complete(ReadinessImportResult.Code.INTERNAL_ERROR,false,false,System.currentTimeMillis());Diagnostics.readinessFetch(context,trace);
                ReadinessImportResult result=new ReadinessImportResult(receipt,ReadinessImportResult.Code.INTERNAL_ERROR,null,System.currentTimeMillis()/1000,"import",BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE);
                if(product==null)product=new ReadinessProduct(null,new ReadinessReceiptStore(context),BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE);
                product.record(result);Diagnostics.readinessResult(context,result.code());
            }
            finally{pending.complete(new Selection(attempted,selected,availabilityFailure));if(selected!=null)Arrays.fill(selected,(byte)0);}
        },"friends-readiness").start();
        return pending;
    }
    static String summary(Context context){
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            synchronized(RestrictedVault.LOCK){OwnerPrewarmReceipt receipt=observation;return cache(context,identity).summary()+"\nrefresh: "+refresh+(receipt==null?"":"\nowner_acceptance: "+receipt.summary());}
        }catch(Exception failure){return "NOT READY — identity unavailable";}
    }
}
