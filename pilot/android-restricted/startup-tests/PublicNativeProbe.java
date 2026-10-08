package com.familyconnect.app;

import android.content.Context;
import android.net.VpnService;
import java.nio.file.Path;
import org.json.JSONObject;

public final class PublicNativeProbe {
    public static void main(String[] arguments) throws Exception {
        Context context=new Context(Path.of(arguments[0]).toFile());
        NativeRestricted.load();
        long handle=NativeRestricted.begin("/deadline","auto","127.0.0.1:53",new VpnService());
        if(handle<=0)throw new AssertionError("Public startup rejected");
        try {
            StartupDiagnostics.begin(context,handle);
            long limit=System.nanoTime()+5_000_000_000L;
            while(NativeRestricted.state(handle)==0 && System.nanoTime()<limit)Thread.sleep(1);
            if(NativeRestricted.state(handle)!=3)throw new AssertionError("Public legacy failure state changed");
            JSONObject stats=new JSONObject(NativeRestricted.stats(handle));
            if(stats.has("owner_startup"))throw new AssertionError("Public native exposes owner fields");
            StartupDiagnostics.capture(context,handle,stats);
            if(StartupDiagnostics.rejected(handle,ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE).getCause()!=null)throw new AssertionError("Public typed diagnostic exposed");
        } finally {
            if(!NativeRestricted.stop(handle))throw new AssertionError("Public native stop failed");
            StartupDiagnostics.stopped(context,handle);
        }
        if(!new JSONObject(NativeRestricted.stats(handle)).toString().equals("{}"))throw new AssertionError("Public terminal retained");
        if(context.getNoBackupFilesDir().list().length!=0)throw new AssertionError("Public diagnostic file created");
        System.out.println("PASS actual default Go/JNI + public Java shim: no owner fields, cause, or file");
    }
}
