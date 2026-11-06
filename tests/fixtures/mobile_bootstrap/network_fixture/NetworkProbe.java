package com.familyconnect.app;
import android.net.*;
public class NetworkProbe {
    private static final String URL="https://127.0.0.1:1/friends/restricted-readiness/challenge";
    private static void require(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] arguments)throws Exception{
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
        context.manager.networks=new Network[]{vpn,cell};
        ChatNetworkAndroid provisioning=new ChatNetworkAndroid(context);
        require(provisioning.provisioningResolver().equals("192.0.2.53:53"));
        require(provisioning.protect(43)&&cell.bound==2&&vpn.bound==0);
        cell.alive=false;wifi.alive=true;context.manager.networks=new Network[]{vpn,wifi};
        require(!provisioning.protect(44)&&wifi.bound==0&&vpn.bound==0);
        require(new ChatNetworkAndroid(context).provisioningResolver().equals("192.0.2.53:53"));
        System.out.println("PASS: actual ChatNetworkAndroid, handoff before/during/after ready, TUN excluded, fresh network per call, no lost-network fallback into VPN. Android stubs only; no physical cellular proof.");
        System.out.println("PASS: provisioning uses physical-network DNS and pins that Network for its lifetime; lost pinned Network fails closed, a new request discovers afresh.");
    }
}
