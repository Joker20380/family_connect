package com.familyconnect.app;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.ParcelFileDescriptor;
import java.io.IOException;

/** JNI callback. Every mailbox socket must bind before connecting. */
public final class ChatNetworkAndroid {
    private final Context context;
    private Network provisioningNetwork;
    private String provisioningType="NONE";
    private long bindAt;
    private boolean bindAvailable;
    private String bindResult="NOT_RUN";
    private String bindOperation="NOT_RUN";
    private String bindError="NONE";
    private int bindErrno;
    private String resolverClass="NONE";
    ChatNetworkAndroid(Context context) { this.context = context.getApplicationContext(); }

    boolean available() {
        ConnectivityManager manager = context.getSystemService(ConnectivityManager.class);
        if (manager == null) return false;
        for (Network network : manager.getAllNetworks()) {
            NetworkCapabilities caps = manager.getNetworkCapabilities(network);
            if (caps != null && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)
                    && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) return true;
        }
        return false;
    }

    javax.net.ssl.HttpsURLConnection openHttps(String url)throws IOException {
        return openHttps(url,null);
    }
    javax.net.ssl.HttpsURLConnection openHttps(String url,ReadinessFetchTrace trace)throws IOException {
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        if(manager!=null)for(Network network:manager.getAllNetworks()){
            NetworkCapabilities caps=manager.getNetworkCapabilities(network);
            if(caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)){
                if(trace!=null)trace.network(caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?"CELLULAR":caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"WIFI":caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)?"ETHERNET":"OTHER",network.getNetworkHandle());
                return (javax.net.ssl.HttpsURLConnection)network.openConnection(new java.net.URL(url));
            }
        }
        if(trace!=null)trace.network("NONE",0);
        throw new IOException("Underlying network unavailable");
    }

    public synchronized boolean bindSocket(int fd) {
        ConnectivityManager manager = context.getSystemService(ConnectivityManager.class);
        if (manager == null) return false;
        if(provisioningNetwork!=null){
            NetworkCapabilities caps=manager.getNetworkCapabilities(provisioningNetwork);
            bindAt=android.os.SystemClock.elapsedRealtime();
            bindOperation="NETWORK_CHECK";bindError="NONE";bindErrno=0;
            bindAvailable=caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
            if(!bindAvailable){bindResult="NETWORK_UNAVAILABLE";return false;}
            bindOperation="FD_DUP";
            try(ParcelFileDescriptor socket=ParcelFileDescriptor.fromFd(fd)){bindOperation="NETWORK_BIND";provisioningNetwork.bindSocket(socket.getFileDescriptor());bindResult="BOUND";return true;}
            catch(IOException unavailable){
                bindResult="IO";bindError=unavailable instanceof java.net.SocketException?"SOCKET":"IO";
                Throwable cause=unavailable;
                for(int depth=0;cause!=null&&depth<4;depth++,cause=cause.getCause())if(cause instanceof android.system.ErrnoException){
                    int code=((android.system.ErrnoException)cause).errno;
                    if(code>0&&code<4096)bindErrno=code;
                    break;
                }
                return false;
            }
            catch(SecurityException unavailable){bindResult="SECURITY";bindError="SECURITY";return false;}
        }
        for (Network network : manager.getAllNetworks()) {
            NetworkCapabilities caps = manager.getNetworkCapabilities(network);
            if (caps == null || !caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)
                    || !caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) continue;
            try (ParcelFileDescriptor socket = ParcelFileDescriptor.fromFd(fd)) {
                network.bindSocket(socket.getFileDescriptor());
                return true;
            } catch (IOException | SecurityException unavailable) { /* Try another underlying network. */ }
        }
        return false;
    }

    public boolean protect(int fd) { return bindSocket(fd); }

    synchronized String provisioningResolver()throws IOException{
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        if(manager!=null)for(Network network:manager.getAllNetworks()){
            NetworkCapabilities caps=manager.getNetworkCapabilities(network);
            android.net.LinkProperties link=manager.getLinkProperties(network);
            if(caps==null||link==null||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))continue;
            for(java.net.InetAddress address:link.getDnsServers())if(address instanceof java.net.Inet4Address){provisioningNetwork=network;resolverClass=address.isLoopbackAddress()?"LOOPBACK":address.isSiteLocalAddress()?"PRIVATE_IPV4":"OTHER_IPV4";provisioningType=caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?"CELLULAR":caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"WIFI":caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)?"ETHERNET":"OTHER";return address.getHostAddress()+":53";}
        }
        throw new IOException("Physical IPv4 resolver unavailable");
    }
    synchronized com.google.gson.JsonObject provisioningDiagnostic(){
        com.google.gson.JsonObject value=new com.google.gson.JsonObject();
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        NetworkCapabilities caps=manager==null||provisioningNetwork==null?null:manager.getNetworkCapabilities(provisioningNetwork);
        value.addProperty("type",provisioningType);value.addProperty("handle",provisioningNetwork==null?0:provisioningNetwork.getNetworkHandle());
        value.addProperty("available",caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET));
        value.addProperty("resolver",provisioningNetwork==null?"NONE":"NETWORK_IPV4_GO_RESOLVER");
        value.addProperty("resolver_class",resolverClass);
        value.addProperty("observed_ms",android.os.SystemClock.elapsedRealtime());value.addProperty("bind_ms",bindAt);value.addProperty("bind_available",bindAvailable);value.addProperty("bind_result",bindResult);
        value.addProperty("bind_operation",bindOperation);value.addProperty("bind_error",bindError);value.addProperty("bind_errno",bindErrno);
        return value;
    }
}
