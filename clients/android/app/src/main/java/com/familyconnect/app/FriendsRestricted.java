package com.familyconnect.app;

import android.content.Context;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicBoolean;

final class FriendsRestricted {
    private static final AtomicBoolean running=new AtomicBoolean();
    static volatile String refresh="NOT_ATTEMPTED";
    static volatile boolean denied;
    static RestrictedCache cache(Context context,ControlIdentity identity)throws Exception{
        byte[] publicIdentity=identity.publicIdentity(),anchor=ControlTrust.anchor(context);
        return new RestrictedCache(new RestrictedVault(context),raw->{NativeRestricted.load();return NativeRestricted.validateDelivery(raw,publicIdentity,anchor);});
    }
    static void prewarm(Context source){
        if(!source.getPackageName().equals("com.familyconnect.app.friends")||!running.compareAndSet(false,true))return;
        Context context=source.getApplicationContext();
        new Thread(()->{
            try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
                RestrictedCache cache=cache(context,identity);
                synchronized(RestrictedVault.LOCK){if(!cache.attempt(System.currentTimeMillis()/1000))return;}
                refresh="IN_PROGRESS";
                try {
                    byte[] response=new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+30000).restrictedReadiness(identity);
                    try{synchronized(RestrictedVault.LOCK){cache.accept(response);}denied=false;refresh="SUCCESS";}finally{Arrays.fill(response,(byte)0);}
                }catch(FriendsAccessAndroid.Denied rejection){denied=true;synchronized(RestrictedVault.LOCK){cache.denied();}refresh="AUTHORIZATION_REJECTED";}
                catch(Exception | LinkageError failure){refresh="UNAVAILABLE";}
            }catch(Exception | LinkageError failure){refresh="UNAVAILABLE";}
            finally{running.set(false);}
        },"friends-readiness").start();
    }
    static String summary(Context context){
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            synchronized(RestrictedVault.LOCK){return cache(context,identity).summary()+"\nrefresh: "+refresh;}
        }catch(Exception failure){return "NOT READY — identity unavailable";}
    }
}
