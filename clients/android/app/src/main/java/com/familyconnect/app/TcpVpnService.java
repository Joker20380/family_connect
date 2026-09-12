package com.familyconnect.app;
import android.net.VpnService;
import android.content.Intent;
import java.util.concurrent.CompletableFuture;
public final class TcpVpnService extends VpnService {
    static volatile CompletableFuture<TcpVpnService> ready=new CompletableFuture<>();
    volatile Runnable revoked;
    @Override public void onCreate(){super.onCreate();ready.complete(this);}
    @Override public void onRevoke(){Runnable callback=revoked;if(callback!=null)callback.run();super.onRevoke();}
    @Override public void onDestroy(){Runnable callback=revoked;if(callback!=null)callback.run();ready=new CompletableFuture<>();super.onDestroy();}
}
