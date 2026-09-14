package com.familyconnect.app;

import android.content.Context;
import android.net.Network;
import java.net.URL;
import java.io.InputStream;
import javax.net.ssl.HttpsURLConnection;

/** DNS plus HTTPS on the exact VPN Network; never retries on the default route. */
final class ControlTrafficHealth {
    private final VpnHealth dns;
    private volatile HttpsURLConnection active;
    private volatile boolean cancelled;
    ControlTrafficHealth(Context context){dns=new VpnHealth(context);}
    synchronized void cancel(){cancelled=true;dns.cancel();if(active!=null)active.disconnect();}
    private synchronized boolean own(HttpsURLConnection connection){
        if(cancelled){connection.disconnect();return false;}active=connection;return true;
    }
    boolean check(String source){
        android.os.Handler timer=new android.os.Handler(android.os.Looper.getMainLooper());
        Runnable timeout=this::cancel;timer.postDelayed(timeout,15000);
        try{return checkBound(source);}finally{timer.removeCallbacks(timeout);}
    }
    private boolean checkBound(String source){
        if(cancelled||!dns.check(source))return false;
        Network network=dns.find(source);if(network==null||cancelled)return false;
        HttpsURLConnection connection=null;
        try {
            connection=(HttpsURLConnection)network.openConnection(new URL("https://www.cloudflare.com/cdn-cgi/trace"));
            if(!own(connection))return false;
            connection.setConnectTimeout(5000);connection.setReadTimeout(5000);connection.setInstanceFollowRedirects(false);
            if(connection.getResponseCode()!=200)return false;
            int count=0,n;byte[] buffer=new byte[512];
            try(InputStream input=connection.getInputStream()){
                while((n=input.read(buffer))!=-1){count+=n;if(count>4096||cancelled)return false;}
            }
            return count>0&&!cancelled&&network.equals(dns.find(source));
        }catch(Exception failure){return false;}
        finally{if(connection!=null)connection.disconnect();active=null;}
    }
}
