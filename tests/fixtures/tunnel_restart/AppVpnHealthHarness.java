package com.familyconnect.app;

import android.content.Context;
import android.net.ConnectivityManager;
import android.os.SystemClock;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

public final class AppVpnHealthHarness {
    private static String answer(String encoded){
        byte[] reply=java.util.Base64.getDecoder().decode(encoded);reply[2]=(byte)0x81;reply[3]=(byte)0x83;
        return java.util.Base64.getEncoder().encodeToString(reply);
    }
    private static void require(boolean value){if(!value)throw new AssertionError("CARRIER_HEALTH_CONTRACT");}
    public static void main(String[] arguments){
        ConnectivityManager manager=new ConnectivityManager();manager.current=null;
        Context context=new Context(manager);AtomicInteger calls=new AtomicInteger();
        VpnHealth healthy=new VpnHealth(context,(query,budget)->{calls.incrementAndGet();require(budget>0&&budget<=2500);return answer(query);});
        require(healthy.check("10.79.0.2"));require(calls.get()==1);
        require(!new VpnHealth(context,(query,budget)->null).check("10.79.0.2"));
        require(!new VpnHealth(context,(query,budget)->{throw new IllegalStateException();}).check("10.79.0.2"));
        require(!new VpnHealth(context,(query,budget)->answer(java.util.Base64.getEncoder().encodeToString(VpnHealth.query(0,"different")))).check("10.79.0.2"));
        AtomicReference<VpnHealth> cancelled=new AtomicReference<>();
        cancelled.set(new VpnHealth(context,(query,budget)->{cancelled.get().cancel();return answer(query);}));
        require(!cancelled.get().check("10.79.0.2"));
        require(!new VpnHealth(context,(query,budget)->{try{Thread.sleep(25);}catch(InterruptedException failure){Thread.currentThread().interrupt();}return answer(query);}).check("10.79.0.2",SystemClock.elapsedRealtime()+5));
        healthy.cancel();require(!healthy.check("10.79.0.2"));require(calls.get()==1);
        require(!new VpnHealth(context,(query,budget)->{calls.incrementAndGet();return answer(query);}).check("10.79.0.2",SystemClock.elapsedRealtime()-1));
        require(calls.get()==1&&ConnectivityManager.bindings.get()==0);
        System.out.println("PASS_CARRIER_HEALTH_8_SCENARIOS_NO_UNDERLAY");
    }
}
