package com.familyconnect.app;

import android.content.Context;
import android.net.*;
import android.os.ParcelFileDescriptor;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import com.google.gson.JsonObject;
import java.io.*;
import java.util.Base64;
import java.util.concurrent.atomic.AtomicBoolean;

/** One bounded RNS exchange session; Java retains device secrets and owns VPN mutations. */
final class ControlRnsAndroid implements ControlCarrier.Wire,AutoCloseable {
    private static final Object PYTHON_START=new Object();
    private final Context context;private final AtomicBoolean cancelled=new AtomicBoolean();private PyObject channel;
    ControlRnsAndroid(Context context){this.context=context.getApplicationContext();}
    public static final class Callbacks {
        private final Context context;private final AtomicBoolean stop;
        Callbacks(Context context,AtomicBoolean stop){this.context=context;this.stop=stop;}
        public boolean cancelled(){return stop.get();}
        public boolean bindSocket(int fd){
            if(stop.get())return false;
            ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
            for(Network network:manager.getAllNetworks()){
                NetworkCapabilities caps=manager.getNetworkCapabilities(network);
                if(caps==null||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))continue;
                try(ParcelFileDescriptor socket=ParcelFileDescriptor.fromFd(fd)){
                    network.bindSocket(socket.getFileDescriptor());return !stop.get();
                }catch(IOException unavailable){}
            }
            return false; // Never fall back into the VPN whose config is being recovered.
        }
    }
    void open()throws Exception {
        JsonObject bootstrap;
        try(InputStream in=context.getAssets().open("rns-relay.json")){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[512];int n;while((n=in.read(buffer))!=-1){if(bytes.size()+n>2048)throw new IOException("Relay bootstrap too large");bytes.write(buffer,0,n);}
            bootstrap=ControlJson.parse(bytes.toByteArray()).getAsJsonObject();
        }
        ControlJson.fields(bootstrap,"host port provider_public");
        synchronized(PYTHON_START){if(!Python.isStarted())Python.start(new AndroidPlatform(context));}
        if(cancelled())throw new IOException("RNS cancelled");
        channel=Python.getInstance().getModule("fc_rns_transport").callAttr("Channel",
            new File(context.getNoBackupFilesDir(),"rns-control").getAbsolutePath(),ControlJson.text(bootstrap.get("host")),
            ControlJson.integer(bootstrap.get("port"),1),ControlJson.text(bootstrap.get("provider_public")),new Callbacks(context,cancelled));
    }
    public boolean cancelled(){return cancelled.get();}
    void cancel(){cancelled.set(true);}
    public byte[] request(String path,byte[] raw)throws Exception {
        if(channel==null||cancelled())throw new IOException("RNS unavailable");
        String encoded=channel.callAttr("request",path,Base64.getEncoder().encodeToString(raw)).toString();
        if(encoded.length()>87384)throw new IOException("RNS reply too large");return ControlProtocol.base64(encoded,true);
    }
    public void close(){cancel();if(channel!=null){try{channel.callAttr("close");}finally{channel.close();channel=null;}}}
}
