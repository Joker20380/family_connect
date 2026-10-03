package com.familyconnect.app;

import android.content.Context;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicBoolean;

final class FriendsRestricted {
    private static final AtomicBoolean running=new AtomicBoolean();
    private static final AtomicBoolean reconciled=new AtomicBoolean();
    static volatile String refresh="NOT_ATTEMPTED";
    static volatile boolean denied;
    private static volatile OwnerPrewarmReceipt observation;
    static RestrictedCache cache(Context context,ControlIdentity identity)throws Exception{
        byte[] publicIdentity=identity.publicIdentity(),anchor=ControlTrust.anchor(context);
        return RestrictedCache.detailed(new RestrictedVault(context),raw->{NativeRestricted.load();int code=NativeRestricted.validationCode(raw,publicIdentity,anchor);return code==0?ReadinessImportResult.Code.READY:code==2?ReadinessImportResult.Code.BOOTSTRAP_VALIDATION_FAILED:ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED;});
    }
    static void prewarm(Context source){
        if(!source.getPackageName().equals("com.familyconnect.app.friends")||!running.compareAndSet(false,true))return;
        Context context=source.getApplicationContext();
        new Thread(()->{
            OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
            ReadinessProduct product=null;
            try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
                RestrictedCache cache=cache(context,identity);
                product=new ReadinessProduct(cache,new ReadinessReceiptStore(context),BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE);
                if(reconciled.compareAndSet(false,true)){
                    ReadinessImportResult restored;OwnerPrewarmReceipt previous;
                    synchronized(RestrictedVault.LOCK){restored=product.restart(System.currentTimeMillis()/1000);previous=cache.context();}
                    Diagnostics.readinessResult(context,restored.code());
                    if(previous==null)product.record(restored);
                    else product.publish(restored,payload->new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+15000).readinessAck(identity,payload));
                }
                synchronized(RestrictedVault.LOCK){if(!cache.attempt(System.currentTimeMillis()/1000))return;}
                refresh="IN_PROGRESS";
                observation=receipt;ReadinessImportResult result;
                try {
                    byte[] response=new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+30000).restrictedReadiness(identity,receipt);
                    try{synchronized(RestrictedVault.LOCK){result=product.imported(response,receipt,System.currentTimeMillis()/1000);}
                        if(result.code()==ReadinessImportResult.Code.READY){receipt.imported(response);denied=false;refresh="SUCCESS";}
                        else{receipt.failed();refresh=result.code().name();}
                    }finally{Arrays.fill(response,(byte)0);}
                }catch(FriendsReadinessProtocol.ChallengeFailure failure){receipt.failed();ReadinessImportResult.Code code=ReadinessImportResult.Code.FETCH_FAILED;
                    if(failure.code==FriendsReadinessProtocol.ChallengeCode.CHALLENGE_UNAUTHORIZED){denied=true;code=ReadinessImportResult.Code.AUTHORIZATION_REJECTED;
                        try{synchronized(RestrictedVault.LOCK){cache.denied();}}catch(Exception storage){code=ReadinessImportResult.Code.PERSISTENCE_FAILED;}}
                    result=product.failed(receipt,code,System.currentTimeMillis()/1000);refresh=failure.code.name();
                }catch(FriendsAccessAndroid.Denied rejection){receipt.failed();denied=true;ReadinessImportResult.Code code=ReadinessImportResult.Code.AUTHORIZATION_REJECTED;
                    try{synchronized(RestrictedVault.LOCK){cache.denied();}}catch(Exception failure){code=ReadinessImportResult.Code.PERSISTENCE_FAILED;}
                    result=product.failed(receipt,code,System.currentTimeMillis()/1000);refresh="AUTHORIZATION_REJECTED";
                }catch(Exception | LinkageError failure){receipt.failed();result=product.failed(receipt,ReadinessImportResult.Code.FETCH_FAILED,System.currentTimeMillis()/1000);refresh="UNAVAILABLE";}
                Diagnostics.readinessResult(context,result.code());
                product.publish(result,payload->new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+15000).readinessAck(identity,payload));
            }catch(Exception | LinkageError failure){refresh="UNAVAILABLE";
                ReadinessImportResult result=new ReadinessImportResult(receipt,ReadinessImportResult.Code.INTERNAL_ERROR,null,System.currentTimeMillis()/1000,"import",BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE);
                if(product==null)product=new ReadinessProduct(null,new ReadinessReceiptStore(context),BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE);
                product.record(result);Diagnostics.readinessResult(context,result.code());
            }
            finally{running.set(false);}
        },"friends-readiness").start();
    }
    static String summary(Context context){
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            synchronized(RestrictedVault.LOCK){OwnerPrewarmReceipt receipt=observation;return cache(context,identity).summary()+"\nrefresh: "+refresh+(receipt==null?"":"\nowner_acceptance: "+receipt.summary());}
        }catch(Exception failure){return "NOT READY — identity unavailable";}
    }
}
