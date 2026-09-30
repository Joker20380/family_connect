package com.familyconnect.app;

import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.VpnService;
import android.os.ParcelFileDescriptor;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.util.concurrent.TimeUnit;

final class AutomaticVpnOwner {
    private final Context context;
    private TcpVpnService service;
    private ParcelFileDescriptor tun;
    private String resolver;
    AutomaticVpnOwner(Context context) { this.context=context; }
    void open(Runnable revoked) throws Exception {
        if(service!=null)throw new IllegalStateException("Owner already open");
        if(VpnService.prepare(context)!=null)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.AUTH);
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        Network active=manager.getActiveNetwork();
        NetworkCapabilities current=manager.getNetworkCapabilities(active);
        if(current!=null&&current.hasTransport(NetworkCapabilities.TRANSPORT_VPN))
            throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.CONFIGURATION);
        LinkProperties link=manager.getLinkProperties(active);
        if(link!=null)for(InetAddress address:link.getDnsServers())if(address instanceof Inet4Address) {
            resolver=address.getHostAddress()+":53";break;
        }
        context.startService(new Intent(context,TcpVpnService.class));
        service=TcpVpnService.ready.get(3,TimeUnit.SECONDS);service.revoked=revoked;
        replace(builder());
    }
    TcpVpnService service() { return service; }
    String resolver() throws ConnectivityOrchestrator.Rejected {
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        resolver=null;
        for(Network network:manager.getAllNetworks()) {
            NetworkCapabilities capabilities=manager.getNetworkCapabilities(network);
            LinkProperties link=manager.getLinkProperties(network);
            if(capabilities==null||!capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)||
                !capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)||link==null)continue;
            for(InetAddress address:link.getDnsServers())if(address instanceof Inet4Address) { resolver=address.getHostAddress()+":53";break; }
            if(resolver!=null)break;
        }
        if(resolver==null)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.TRANSPORT_UNAVAILABLE);
        return resolver;
    }
    VpnService.Builder builder() {
        return service.new Builder().setSession("Family Connect").setMtu(1280)
            .addAddress("10.79.0.2",32).addAddress("fd79:fc::2",128)
            .addRoute("0.0.0.0",0).addRoute("::",0).addDnsServer("10.79.0.1").setBlocking(false);
    }
    ParcelFileDescriptor replace(VpnService.Builder builder) throws Exception {
        ParcelFileDescriptor next=builder.establish();
        if(next==null)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.AUTH);
        ParcelFileDescriptor previous=tun;tun=next;
        if(previous!=null)previous.close();
        return next;
    }
    void block() throws Exception { if(service!=null)replace(builder()); }
    void close() throws Exception {
        if(tun!=null) { tun.close();tun=null; }
        if(service!=null) { service.revoked=null;service.stopSelf();service.stopped.get(3,TimeUnit.SECONDS);service=null; }
    }
}
