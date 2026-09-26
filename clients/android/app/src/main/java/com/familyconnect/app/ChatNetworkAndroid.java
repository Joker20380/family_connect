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
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        if(manager!=null)for(Network network:manager.getAllNetworks()){
            NetworkCapabilities caps=manager.getNetworkCapabilities(network);
            if(caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))
                return (javax.net.ssl.HttpsURLConnection)network.openConnection(new java.net.URL(url));
        }
        throw new IOException("Underlying network unavailable");
    }

    public boolean bindSocket(int fd) {
        ConnectivityManager manager = context.getSystemService(ConnectivityManager.class);
        if (manager == null) return false;
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
}
