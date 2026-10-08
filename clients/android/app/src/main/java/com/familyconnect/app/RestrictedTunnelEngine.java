package com.familyconnect.app;

import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.NetworkCapabilities;
import android.net.VpnService;
import android.os.Debug;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import java.io.File;
import java.io.FileOutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import org.json.JSONObject;

final class RestrictedTunnelEngine implements TunnelEngine {
    private final Context context;
    private final BooleanSupplier cancelled;
    private final Consumer<Boolean> state;
    private TcpVpnService service;
    private ParcelFileDescriptor tun;
    private long handle;
    private volatile boolean revoked;
    private final AutomaticVpnOwner automaticOwner;
    private final long connectDeadline;

    RestrictedTunnelEngine(Context context, BooleanSupplier cancelled, Consumer<Boolean> state) {
        this(context,cancelled,state,null,Long.MAX_VALUE);
    }

    RestrictedTunnelEngine(Context context, BooleanSupplier cancelled, Consumer<Boolean> state,AutomaticVpnOwner owner,long deadline) {
        this.context=context; this.cancelled=cancelled; this.state=state;
        automaticOwner=owner;connectDeadline=deadline;
    }

    public void up(String control) throws Exception {
        checkAccess();
        if (automaticOwner==null && (context.getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE)==0)
            throw new IllegalStateException("Diagnostic only");
        if (VpnService.prepare(context)!=null) throw new IllegalStateException("VPN permission required");
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        NetworkCapabilities capabilities=manager.getNetworkCapabilities(manager.getActiveNetwork());
        LinkProperties link=manager.getLinkProperties(manager.getActiveNetwork());
        if (automaticOwner==null && (capabilities==null || capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN) || link==null))
            throw new IllegalStateException("Direct underlay required");
        String resolver=null;
        if(automaticOwner!=null)resolver=automaticOwner.resolver();
        else for (InetAddress address:link.getDnsServers()) if (address instanceof Inet4Address) { resolver=address.getHostAddress()+":53"; break; }
        if (resolver==null) throw new IllegalStateException("IPv4 underlay resolver required");
        try { NativeRestricted.load(); }
        catch(UnsatisfiedLinkError absent) { throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE); }
        if(automaticOwner!=null)service=automaticOwner.service();
        else {
            context.startService(new Intent(context,TcpVpnService.class));
            service=TcpVpnService.ready.get(3,TimeUnit.SECONDS);
            service.revoked=()->{revoked=true; state.accept(false);};
        }
        File directory=new File(context.getNoBackupFilesDir(),"restricted");
        if(context.getPackageName().equals("com.familyconnect.app.friends")) {
            try(ControlIdentity identity=new FriendsIdentityVault(context).load()) {
                byte[] response;
                synchronized(RestrictedVault.LOCK){response=FriendsRestricted.cache(context,identity).usable();}
                Diagnostics.readiness(context,response!=null);
                if(response==null)throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE);
                byte[] full=identity.material(),material=java.util.Arrays.copyOf(full,64);java.util.Arrays.fill(full,(byte)0);
                try{checkAccess();handle=NativeRestricted.beginReady(response,material,ControlTrust.anchor(context),resolver,service);}
                finally{java.util.Arrays.fill(material,(byte)0);java.util.Arrays.fill(response,(byte)0);}
            }
        } else {
            if (!directory.isDirectory()) throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE);
            checkAccess();
            handle=NativeRestricted.begin(directory.getAbsolutePath(),automaticOwner==null?control:"auto",resolver,service);
        }
        if (handle<=0) throw new IllegalStateException("Restricted startup rejected");
        StartupDiagnostics.begin(context,handle);
        long deadline=Math.min(connectDeadline,SystemClock.elapsedRealtime()+200000);
        int phase;
        while ((phase=NativeRestricted.state(handle))==0 && SystemClock.elapsedRealtime()<deadline && !cancelled.getAsBoolean() && !authorizationDenied()) Thread.sleep(100);
        evidence();
        checkAccess();
        if (!control.isEmpty() && phase==4) return;
        if (phase!=1) throw StartupDiagnostics.rejected(handle,phase==5?ConnectivityOrchestrator.Failure.AUTH:ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE);
        if(automaticOwner!=null)tun=automaticOwner.replace(automaticOwner.builder());
        else tun=service.new Builder().setSession("Family restricted diagnostic").setMtu(1280)
            .addAddress("10.79.0.2",32).addAddress("fd79:fc::2",128)
            .addRoute("0.0.0.0",0).addRoute("::",0).addDnsServer("10.79.0.1")
            .setBlocking(false).establish();
        if (tun==null || revoked || !NativeRestricted.attach(handle,tun.getFd())) throw new IllegalStateException("Packet attachment failed");
        evidence();
        state.accept(true);
    }

    boolean healthy() { return handle>0 && NativeRestricted.state(handle)==2 && (!context.getPackageName().equals("com.familyconnect.app.friends") || !FriendsRestricted.denied); }

    private boolean authorizationDenied() {
        return revoked||(context.getPackageName().equals("com.familyconnect.app.friends")&&FriendsRestricted.denied);
    }

    private void checkAccess() throws ConnectivityOrchestrator.Rejected {
        if(authorizationDenied())throw StartupDiagnostics.rejected(handle,ConnectivityOrchestrator.Failure.AUTH);
        if(cancelled.getAsBoolean())throw StartupDiagnostics.rejected(handle,ConnectivityOrchestrator.Failure.CANCELLED);
    }

    ConnectivityOrchestrator.Failure connectionFailure() {
        int phase=-1;
        String snapshot=null;
        try {
            if(handle>0) {
                phase=NativeRestricted.state(handle);
                snapshot=NativeRestricted.stats(handle);
                evidence(new JSONObject(snapshot));
            }
        } catch(Exception | LinkageError unavailable) {}
        return RestrictedRecovery.failure(phase,cancelled.getAsBoolean(),authorizationDenied(),snapshot);
    }

    static void failure(Context context,Throwable failure) {
        try {
            JSONObject record=new JSONObject();record.put("state",3);record.put("java_failure",failure.getClass().getSimpleName());
            org.json.JSONArray frames=new org.json.JSONArray();
            for(StackTraceElement frame:failure.getStackTrace())if(frame.getClassName().startsWith("com.familyconnect.app."))frames.put(frame.toString());
            record.put("frames",frames);
            try(FileOutputStream output=context.openFileOutput("restricted-evidence.jsonl",Context.MODE_APPEND)) {
                output.write((record.toString()+"\n").getBytes(StandardCharsets.UTF_8));
            }
        }catch(Exception ignored){}
    }

    void evidence() throws Exception {
        if (handle<=0) return;
        evidence(new JSONObject(NativeRestricted.stats(handle)));
    }

    private void evidence(JSONObject snapshot) throws Exception {
        StartupDiagnostics.capture(context,handle,snapshot);
        File output=new File(context.getFilesDir(),"restricted-evidence.jsonl");
        snapshot.put("authorization_denied",FriendsRestricted.denied);
        Diagnostics.nativeStats(context,snapshot);
        if (output.length()>1024*1024) return;
        snapshot.put("elapsed_ms",SystemClock.elapsedRealtime());
        snapshot.put("pss_kib",Debug.getPss());
        snapshot.put("cpu_ms",android.os.Process.getElapsedCpuTime());
        snapshot.put("owner_status",ConnectionService.status);
        snapshot.put("owner_health",ConnectionService.healthStatus);
        try (FileOutputStream stream=new FileOutputStream(output,true)) {
            stream.write((snapshot.toString()+"\n").getBytes(StandardCharsets.UTF_8));
        }
    }

    public void down() throws Exception {
        if (handle>0) {
            try { evidence(); }catch(Exception ignored){}
            boolean stopped=NativeRestricted.stop(handle);
            StartupDiagnostics.stopped(context,handle);
            Diagnostics.cleanup(context,stopped);
            if (!stopped) throw new IllegalStateException("Restricted cleanup failed");
            handle=0;
        }
        if (tun!=null) { if(automaticOwner==null)tun.close(); tun=null; }
        if (service!=null) { if(automaticOwner==null) { service.revoked=null; service.stopSelf(); } service=null; }
        state.accept(false);
    }
}
