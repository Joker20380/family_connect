package com.familyconnect.app;

import android.content.Context;
import android.net.*;
import android.os.ParcelFileDescriptor;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.google.gson.JsonObject;
import java.io.*;
import java.util.Base64;
import java.util.concurrent.atomic.AtomicBoolean;

/** One bounded RNS exchange session; Java retains device secrets and owns VPN mutations. */
final class ControlRnsAndroid implements ControlCarrier.Wire,AutoCloseable {
    private final Context context;private final AtomicBoolean cancelled=new AtomicBoolean();private PyObject channel;
    private final long deadline;
    private ReadinessFetchTrace fetchTrace;
    ControlRnsAndroid(Context context){this(context,Long.MAX_VALUE);}
    ControlRnsAndroid(Context context,long deadline){this.context=context.getApplicationContext();this.deadline=deadline;}
    public static final class Callbacks {
        private final Context context;private final AtomicBoolean stop;private final long deadline;
        private final ReadinessFetchTrace trace;
        Callbacks(Context context,AtomicBoolean stop,long deadline){this(context,stop,deadline,null);}
        Callbacks(Context context,AtomicBoolean stop,long deadline,ReadinessFetchTrace trace){this.context=context;this.stop=stop;this.deadline=deadline;this.trace=trace;}
        public String stopReason(){return ReadinessStop.reason(stop.get(),android.os.SystemClock.elapsedRealtime(),deadline);}
        public boolean cancelled(){return stop.get()||android.os.SystemClock.elapsedRealtime()>=deadline;}
        public boolean bindSocket(int fd){
            if(cancelled())return false;
            ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
            for(Network network:manager.getAllNetworks()){
                NetworkCapabilities caps=manager.getNetworkCapabilities(network);
                if(caps==null||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)||!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))continue;
                try(ParcelFileDescriptor socket=ParcelFileDescriptor.fromFd(fd)){
                    network.bindSocket(socket.getFileDescriptor());
                    if(trace!=null)trace.network(caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?"CELLULAR":caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"WIFI":caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)?"ETHERNET":"OTHER",network.getNetworkHandle());
                    return !cancelled();
                }catch(IOException unavailable){}
            }
            if(trace!=null)trace.network("NONE",0);
            return false; // Never fall back into the VPN whose config is being recovered.
        }
    }
    void open()throws Exception {open(false);}
    void openReadiness(ReadinessFetchTrace trace)throws Exception {fetchTrace=trace;open(true);}
    private void open(boolean readiness)throws Exception {
        JsonObject bootstrap;
        try(InputStream in=context.getAssets().open("rns-relay.json")){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[512];int n;while((n=in.read(buffer))!=-1){if(bytes.size()+n>2048)throw new IOException("Relay bootstrap too large");bytes.write(buffer,0,n);}
            bootstrap=ControlJson.parse(bytes.toByteArray()).getAsJsonObject();
        }
        ControlJson.fields(bootstrap,"host port provider_public");
        PythonRuntimeAndroid.get(context);
        if(readiness)ReadinessStop.check(cancelled.get(),android.os.SystemClock.elapsedRealtime(),deadline);
        else if(cancelled())throw new IOException("RNS cancelled");
        PyObject opened=Python.getInstance().getModule("fc_rns_transport").callAttr(readiness?"readiness_open":"Channel",
            new File(context.getNoBackupFilesDir(),"rns-control").getAbsolutePath(),ControlJson.text(bootstrap.get("host")),
            ControlJson.integer(bootstrap.get("port"),1),ControlJson.text(bootstrap.get("provider_public")),new Callbacks(context,cancelled,deadline,fetchTrace));
        if(readiness){
            java.util.List<PyObject> result=opened.asList();
            if(result.get(0).toString().equals("UNAVAILABLE"))throw new FriendsReadinessProtocol.Unavailable();
            ControlJson.require(result.get(0).toString().equals("AVAILABLE"));channel=result.get(1);
        }else channel=opened;
    }
    public boolean cancelled(){return cancelled.get()||android.os.SystemClock.elapsedRealtime()>=deadline;}
    void cancel(){cancelled.set(true);}
    public byte[] request(String path,byte[] raw)throws Exception {
        if(channel==null||cancelled())throw new IOException("RNS unavailable");
        String encoded=channel.callAttr("request",path,Base64.getEncoder().encodeToString(raw)).toString();
        if(encoded.length()>(ReadinessBootstrapRoute.allowed(path)?120000:87384))throw new IOException("RNS reply too large");return ControlProtocol.base64(encoded,true);
    }
    byte[] requestReadiness(String path,byte[] raw)throws Exception {
        ReadinessStop.check(cancelled.get(),android.os.SystemClock.elapsedRealtime(),deadline);
        if(channel==null)throw new IOException("RNS unavailable");
        java.util.List<PyObject> result=channel.callAttr("readiness_request",path,Base64.getEncoder().encodeToString(raw)).asList();
        if(result.get(0).toString().equals("UNAVAILABLE"))throw new FriendsReadinessProtocol.Unavailable();
        ControlJson.require(result.get(0).toString().equals("AVAILABLE"));
        String encoded=result.get(1).toString();
        if(encoded.length()>120000)throw new IOException("RNS reply too large");
        return ControlProtocol.base64(encoded,true);
    }
    public void close(){cancel();if(channel!=null){try{channel.callAttr("close");}finally{channel.close();channel=null;}}}
}
