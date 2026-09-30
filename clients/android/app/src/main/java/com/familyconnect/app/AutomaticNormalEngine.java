package com.familyconnect.app;

import android.content.Context;
import android.net.VpnService;
import android.os.ParcelFileDescriptor;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import org.amnezia.awg.GoBackend;
import org.amnezia.awg.config.Config;
import org.amnezia.awg.config.InetNetwork;

final class AutomaticNormalEngine implements TunnelEngine {
    private final Context context;
    private final AutomaticVpnOwner owner;
    private final Transport transport;
    private int awg=-1;
    private long tcp;
    String source;
    AutomaticNormalEngine(Context context,AutomaticVpnOwner owner,Transport transport) {
        this.context=context;this.owner=owner;this.transport=transport;
    }
    public void up(String raw) throws Exception {
        String profile=ProfileValidator.validate(raw,transport);
        NativeTcp.load(context);
        if(transport==Transport.TCP) {
            source="10.79.0.2";
            VpnService.Builder builder=owner.service().new Builder().setSession("Family Connect").setMtu(1280)
                .addAddress(source,32).addRoute("0.0.0.0",0).addRoute("::",0)
                .addDnsServer("1.1.1.1").setBlocking(false);
            tcp=NativeTcp.start(owner.replace(builder).getFd(),profile,owner.service());
            if(tcp<=0)throw new ConnectivityOrchestrator.Rejected(tcp==-2?ConnectivityOrchestrator.Failure.CONFIGURATION:ConnectivityOrchestrator.Failure.INTERNAL);
            return;
        }
        Config config=Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8)));
        VpnService.Builder builder=owner.service().new Builder().setSession("Family Connect")
            .setMtu(config.getInterface().getMtu().orElse(1280)).addRoute("0.0.0.0",0).addRoute("::",0).setBlocking(true);
        boolean ipv6=false;
        for(InetNetwork address:config.getInterface().getAddresses()) {
            builder.addAddress(address.getAddress(),address.getMask());
            if(address.getAddress() instanceof java.net.Inet4Address)source=address.getAddress().getHostAddress();else ipv6=true;
        }
        if(source==null)throw new IllegalArgumentException("IPv4 required");
        if(!ipv6)builder.addAddress("fd79:fc::2",128);
        for(java.net.InetAddress address:config.getInterface().getDnsServers())builder.addDnsServer(address.getHostAddress());
        String settings=config.toAwgUserspaceString();
        ParcelFileDescriptor descriptor=owner.replace(builder);
        awg=GoBackend.awgTurnOn("fc-auto",ParcelFileDescriptor.dup(descriptor.getFileDescriptor()).detachFd(),settings);
        if(awg<0)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.INTERNAL);
        int socket4=GoBackend.awgGetSocketV4(awg),socket6=GoBackend.awgGetSocketV6(awg);
        if(socket4<0||!owner.service().protect(socket4)||(socket6>=0&&!owner.service().protect(socket6)))
            throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.INTERNAL);
    }
    public void down() throws Exception {
        if(tcp>0) { if(!NativeTcp.stop(tcp))throw new IllegalStateException("TCP cleanup failed");tcp=0; }
        if(awg>=0) { GoBackend.awgTurnOff(awg);awg=-1; }
    }
}
