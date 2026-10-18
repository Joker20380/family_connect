package com.familyconnect.app;
import android.content.Context;
import android.net.*;
import java.net.*;
import org.json.*;

final class TcpNetworkEvidence {
    static JSONObject snapshot(Context context)throws Exception{
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        JSONObject result=new JSONObject();Network active=manager.getActiveNetwork();
        result.put("default",active==null?"none":active.toString());
        result.put("explicit_bound_network","none: original source-address-only binding");
        result.put("vpn_status",ConnectionService.status);result.put("transport",ConnectionService.activeTransport);
        result.put("health",ConnectionService.healthStatus);result.put("session",ConnectionService.sessionId);
        JSONArray networks=new JSONArray();int count=0;
        for(Network network:manager.getAllNetworks()){
            if(count++>=6)break;
            NetworkCapabilities caps=manager.getNetworkCapabilities(network);LinkProperties link=manager.getLinkProperties(network);
            JSONObject item=new JSONObject().put("id",network.toString());
            if(caps!=null){item.put("vpn",caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN));item.put("internet",caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET));item.put("validated",caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED));}
            if(link!=null){
                String iface=link.getInterfaceName();item.put("iface",iface!=null&&iface.matches("(tun[0-9]{1,2}|eth0|wlan0)")?iface:"other");
                item.put("v4_default",link.getRoutes().stream().anyMatch(route->route.isDefaultRoute()&&route.getDestination().getAddress() instanceof Inet4Address));
                item.put("v6_default",link.getRoutes().stream().anyMatch(route->route.isDefaultRoute()&&route.getDestination().getAddress() instanceof Inet6Address));
                item.put("tcp_source",link.getLinkAddresses().stream().anyMatch(address->address.getAddress().getHostAddress().equals("10.79.0.2")));
            }
            networks.put(item);
        }
        return result.put("networks",networks);
    }
    static JSONArray hostProbe(Context context)throws Exception{
        JSONArray result=new JSONArray();ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);int count=0;
        for(Network network:manager.getAllNetworks()){
            NetworkCapabilities caps=manager.getNetworkCapabilities(network);
            if(caps==null||caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))continue;
            if(count++>=6)break;
            JSONObject item=new JSONObject().put("network",network.toString());
            try(Socket socket=network.getSocketFactory().createSocket()){socket.connect(new InetSocketAddress("10.0.2.2",51902),1000);item.put("connect",true);}
            catch(Exception failure){item.put("connect",false);item.put("error_type",failure.getClass().getSimpleName());}
            result.put(item);
        }
        return result;
    }
    static void emit(JSONObject receipt){
        String value=receipt.toString();if(value.length()>3800)throw new AssertionError("TCP evidence bound exceeded");
        android.util.Log.i("TcpPrimary",value);
    }
}
