package com.familyconnect.app;
import android.net.*;
public class NetworkProbe {
    private static final String URL="https://127.0.0.1:1/friends/restricted-readiness/challenge";
    private static void require(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] arguments)throws Exception{
        for(int sdk:new int[]{27,28,35}){android.os.Build.VERSION.SDK_INT=sdk;probe();}
    }
    private static void probe()throws Exception{
        android.content.Context context=new android.content.Context();
        context.manager=new ConnectivityManager();
        Network wifi=new Network(1),cell=new Network(2),vpn=new Network(3);
        cell.caps.transport=NetworkCapabilities.TRANSPORT_CELLULAR;vpn.caps.notVpn=false;
        ChatNetworkAndroid requests=new ChatNetworkAndroid(context);
        ReadinessFetchTrace trace=new ReadinessFetchTrace();
        context.manager.networks=new Network[]{wifi};
        requests.openHttps(URL,trace).disconnect();require(trace.generation==1);
        context.manager.networks=new Network[]{cell};
        requests.openHttps(URL,trace).disconnect();require(trace.generation==2);
        context.manager.networks=new Network[]{vpn,cell};
        requests.openHttps(URL,trace).disconnect();require(trace.generation==2&&vpn.opened==0);
        context.manager.networks=new Network[]{wifi,cell};
        wifi.beforeOpen=()->{wifi.alive=false;context.manager.networks=new Network[]{vpn,cell};};
        try{requests.openHttps(URL,trace);throw new AssertionError();}catch(java.net.ConnectException expected){}
        requests.openHttps(URL,trace).disconnect();require(trace.generation==2&&vpn.opened==0);
        require(requests.bindSocket(42)&&cell.bound==1&&vpn.bound==0);
        context.manager.networks=new Network[]{vpn};
        require(!requests.available());
        try{requests.openHttps(URL,trace);throw new AssertionError();}catch(java.io.IOException expected){}
        require(trace.generation==0&&trace.type.equals("NONE")&&vpn.opened==0);
        context.manager.networks=new Network[]{cell};
        ChatNetworkAndroid provisioning=new ChatNetworkAndroid(context);
        require(provisioning.provisioningResolver().equals("192.0.2.53:53"));
        require(context.manager.dnsNetwork==cell);
        require(provisioning.protect(43)&&cell.bound==2&&vpn.bound==0);
        com.google.gson.JsonObject selected=provisioning.provisioningDiagnostic();
        require(selected.get("handle").getAsLong()==2&&selected.get("type").getAsString().equals("CELLULAR")&&selected.get("bind_result").getAsString().equals("BOUND"));
        java.net.SocketException rejected=new java.net.SocketException("must not escape into diagnostics");
        rejected.initCause(new android.system.ErrnoException("private syscall details",22));
        cell.bindFailure=rejected;
        require(!provisioning.protect(43));selected=provisioning.provisioningDiagnostic();
        require(selected.get("bind_operation").getAsString().equals("NETWORK_BIND")&&selected.get("bind_errno").getAsInt()==22);
        require(!selected.toString().contains("private")&&!selected.toString().contains("escape"));
        cell.bindFailure=null;android.os.ParcelFileDescriptor.failure=rejected;
        require(!provisioning.protect(43));selected=provisioning.provisioningDiagnostic();
        require(selected.get("bind_operation").getAsString().equals("FD_DUP")&&selected.get("bind_errno").getAsInt()==22);
        android.os.ParcelFileDescriptor.failure=null;
        require(provisioning.protect(43)&&provisioning.provisioningDiagnostic().get("bind_errno").getAsInt()==0);
        cell.alive=false;wifi.alive=true;context.manager.networks=new Network[]{vpn,wifi};
        require(!provisioning.protect(44)&&wifi.bound==0&&vpn.bound==0);
        selected=provisioning.provisioningDiagnostic();
        require(selected.get("handle").getAsLong()==2&&!selected.get("available").getAsBoolean()&&!selected.get("bind_available").getAsBoolean()&&selected.get("bind_result").getAsString().equals("NETWORK_UNAVAILABLE"));
        require(new ChatNetworkAndroid(context).provisioningResolver().equals("192.0.2.53:53"));
        cell.alive=true;cell.caps.foreground=false;
        context.manager.networks=new Network[]{cell,vpn,wifi};
        ChatNetworkAndroid foreground=new ChatNetworkAndroid(context);
        foreground.provisioningResolver();
        require(foreground.provisioningDiagnostic().get("handle").getAsLong()==1);
        require(foreground.protect(45)&&wifi.bound==1);
        cell.caps.foreground=true;wifi.caps.foreground=false;
        require(!foreground.protect(46)&&cell.bound==3);
        ChatNetworkAndroid activeCellular=new ChatNetworkAndroid(context);
        activeCellular.provisioningResolver();
        require(activeCellular.provisioningDiagnostic().get("handle").getAsLong()==2);
        require(activeCellular.protect(47)&&cell.bound==4);
        cell.caps.notRestricted=false;
        require(!activeCellular.protect(48)&&cell.bound==4);
        try{new ChatNetworkAndroid(context).provisioningResolver();throw new AssertionError();}catch(java.io.IOException expected){}
        System.out.println("PASS: actual ChatNetworkAndroid, handoff before/during/after ready, TUN excluded, fresh network per call, no lost-network fallback into VPN. Android stubs only; no physical cellular proof.");
        System.out.println("PASS: provisioning uses physical-network DNS and pins that Network for its lifetime; lost pinned Network fails closed, a new request discovers afresh.");
        System.out.println("PASS: background/restricted networks cannot be pinned; eligible cellular remains usable; demotion fails closed without route fallback.");
    }
}
