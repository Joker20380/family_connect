package com.familyconnect.app;
import android.content.*;
import android.net.VpnService;
import android.os.ParcelFileDescriptor;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
final class TcpTunnelEngine implements TunnelEngine {
    private final Context context;private final Consumer<Boolean> state;
    private TcpVpnService service;private ParcelFileDescriptor tun;private long handle;
    private volatile boolean revoked;
    private final AppVpnAndroid applications;
    TcpTunnelEngine(Context context,Consumer<Boolean> state){this(context,state,new AppVpnAndroid(context,AppVpnPolicy.all()));}
    TcpTunnelEngine(Context context,Consumer<Boolean> state,AppVpnAndroid applications){this.context=context;this.state=state;this.applications=applications;}
    public String probeDns(String query,int budgetMillis){return handle>0?NativeTcp.tcpDns(handle,query,budgetMillis):null;}
    public void up(String raw)throws Exception{
        String profile=TcpProfile.validate(raw);if(VpnService.prepare(context)!=null)throw new IllegalStateException("VPN permission required");
        NativeTcp.load(context);
        context.startService(new Intent(context,TcpVpnService.class));service=TcpVpnService.ready.get(3,TimeUnit.SECONDS);
        service.revoked=()->{revoked=true;state.accept(false);};
        tun=applications.apply(service.new Builder().setSession("Family Connect TCP").setMtu(1280)
            .addAddress("10.79.0.2",32).addAddress("fd79:fc::2",128).addRoute("0.0.0.0",0).addRoute("::",0)
            .addDnsServer("1.1.1.1").setBlocking(false)).establish();
        if(tun==null||revoked)throw new IllegalStateException("VPN unavailable");
        handle=NativeTcp.start(tun.getFd(),profile,service);
        if(handle<=0||revoked){android.util.Log.e("FamilyConnect","TCP startup failed stage="+handle);throw new IllegalStateException("TCP startup failed");}
        state.accept(true);
    }
    public void down()throws Exception{
        if(handle>0){if(!NativeTcp.stop(handle))throw new IllegalStateException("TCP cleanup failed");handle=0;}
        if(tun!=null){tun.close();tun=null;}
        if(service!=null){service.revoked=null;service.stopSelf();service=null;}
        state.accept(false);
    }
}
