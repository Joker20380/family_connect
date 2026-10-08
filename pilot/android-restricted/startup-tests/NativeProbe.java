package com.familyconnect.app;

import android.content.Context;
import android.net.VpnService;
import java.nio.file.Files;
import java.nio.file.Path;
import org.json.JSONObject;

public final class NativeProbe {
    private static native void late(int index);
    private static Context context;
    private static boolean owner;
    private static long live;

    private static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }

    private static long begin(String mode) throws Exception {
        long handle = NativeRestricted.begin("/"+mode, "auto", "127.0.0.1:53", new VpnService());
        require(handle>0,"native begin rejected");
        live=handle;
        StartupDiagnostics.begin(context,handle);
        return handle;
    }

    private static JSONObject finish(long handle, int state) throws Exception {
        long limit = System.nanoTime()+5_000_000_000L;
        while (NativeRestricted.state(handle)==0 && System.nanoTime()<limit) Thread.sleep(1);
        JSONObject stats = new JSONObject(NativeRestricted.stats(handle));
        StartupDiagnostics.capture(context,handle,stats);
        require(NativeRestricted.state(handle)==state,"native state changed; safe result="+stats.optJSONObject("owner_startup"));
        if (!owner) { require(!stats.has("owner_startup"),"public native leaked owner result"); return null; }
        JSONObject result=stats.getJSONObject("owner_startup");
        require(result.getBoolean("complete") && result.getLong("attempt")==handle,"native result unbound");
        return result;
    }

    private static void stop(long handle) throws Exception {
        require(NativeRestricted.stop(handle),"native stop failed");
        live=0;
        StartupDiagnostics.stopped(context,handle);
        require(NativeRestricted.state(handle)==-1,"native owner survived stop");
        if (owner) require(new JSONObject(NativeRestricted.stats(handle)).getJSONObject("owner_startup").getLong("attempt")==handle,"native retention lost on stop");
    }

    public static void main(String[] arguments) throws Exception {
        Throwable primary=null;
        try { run(arguments); }
        catch(Exception | Error failure) { primary=failure; throw failure; }
        finally {
            if(live>0) {
                try { stop(live); }
                catch(Exception | Error cleanup) {
                    if(primary==null)throw cleanup;
                    if(primary!=cleanup)primary.addSuppressed(cleanup);
                }
            }
        }
    }

    private static void run(String[] arguments) throws Exception {
        owner=arguments[0].equals("owner");
        context=new Context(Path.of(arguments[1]).toFile());
        NativeRestricted.load();
        long first=begin("success");
        JSONObject success=finish(first,1);
        if(owner)require(success.getString("status").equals("SUCCEEDED"),"successful startup altered");
        stop(first);
        System.out.println("PASS first startup + native cleanup");
        long second=begin("deadline");
        JSONObject failure=finish(second,3);
        if(owner) {
            require(failure.getString("stage").equals("HELLO_RECEIVE") && failure.getString("cause").equals("DEADLINE"),"primary cause lost through JNI");
            ConnectivityOrchestrator.Rejected rejected=StartupDiagnostics.rejected(second,ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE);
            require(rejected.getMessage().equals("BOOTSTRAP_UNAVAILABLE") && rejected.getCause() instanceof StartupResult.Failure,"Java mapping erased typed result");
            require(((StartupResult.Failure)rejected.getCause()).result.attempt==second,"exception bound to previous attempt");
            ConnectivityOrchestrator.Rejected cancelledCategory=StartupDiagnostics.rejected(second,ConnectivityOrchestrator.Failure.CANCELLED);
            require(cancelledCategory.getMessage().equals("CANCELLED") && ((StartupResult.Failure)cancelledCategory.getCause()).result.cause.equals("DEADLINE"),"cancellation mapping erased preceding primary");
            require(!new JSONObject(NativeRestricted.stats(second)).has("packet"),"unexpected DESCRIPTOR trace");
        }
        stop(second);
        if(owner) {
            for(int index=0;index<256;index++) {
                Files.writeString(Path.of(arguments[1],"diag-ring.json"),"{\"events\":[]}");
                JSONObject retained=new JSONObject(NativeRestricted.stats(second)).getJSONObject("owner_startup");
                require(retained.getString("cause").equals("DEADLINE"),"stats consumed cause");
            }
            java.lang.reflect.Field latest=StartupDiagnostics.class.getDeclaredField("latest");latest.setAccessible(true);latest.set(null,null);
            require(new JSONObject(StartupDiagnostics.read(context)).getJSONObject("result").getLong("attempt")==second,"persisted terminal lost after ring refresh");
        }
        System.out.println("PASS second attempt early HELLO cause + JNI + Java + stop/ring retention");
        long third=begin("success");
        finish(third,1);
        late(0);late(1);
        StartupDiagnostics.begin(context,first);
        if(owner) {
            StartupDiagnostics.capture(context,second,new JSONObject().put("owner_startup",failure));
            require(new JSONObject(StartupDiagnostics.read(context)).getJSONObject("result").getLong("attempt")==third,"stale Java callback poisoned new startup");
            require(new JSONObject(NativeRestricted.stats(third)).getJSONObject("owner_startup").getString("status").equals("SUCCEEDED"),"stale Go callback poisoned new startup");
            require(StartupDiagnostics.rejected(second,ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE).getCause()==null,"old caller received new attempt cause");
        }
        stop(third);
        System.out.println("PASS stale callbacks cannot alter next successful startup");
        long cleanup=begin("cleanup");
        JSONObject cleaned=finish(cleanup,3);
        stop(cleanup);
        if(owner)require(cleaned.getString("cause").equals("DEADLINE"),"cleanup replaced primary");
        long unknown=begin("unknown");
        JSONObject hidden=finish(unknown,3);
        stop(unknown);
        if(owner)require(hidden.getString("cause").equals("UNKNOWN") && !StartupDiagnostics.read(context).contains("PRIVATE"),"unknown error leaked");
        long family=begin("family");
        finish(family,3);
        stop(family);
        System.out.println("PASS cleanup primary + UNKNOWN privacy + legacy native state3");
        long cancelled=begin("cancel");
        stop(cancelled);
        if(owner) {
            JSONObject result=new JSONObject(StartupDiagnostics.read(context)).getJSONObject("result");
            require(result.getString("status").equals("CANCELLED") && result.getString("cause").equals("CANCELLED"),"intentional cancel reported as network failure");
            Path failedPath=Path.of(arguments[1],"not-a-directory");
            Files.writeString(failedPath,"fixture");
            Context failedContext=new Context(failedPath.toFile());
            StartupDiagnostics.begin(failedContext,cancelled+1);
            require(new JSONObject(StartupDiagnostics.read(context)).getString("collection").equals("COLLECTION_ERROR"),"failed pending write exposed stale prior result");
            result.put("attempt",cancelled+1);
            StartupDiagnostics.capture(failedContext,cancelled+1,new JSONObject().put("owner_startup",result));
            JSONObject failedCollection=new JSONObject(StartupDiagnostics.read(failedContext));
            require(failedCollection.getString("collection").equals("COLLECTION_ERROR") && failedCollection.getJSONObject("result").getString("cause").equals("CANCELLED"),"persistence failure erased retained primary");
        }
        System.out.println("PASS bounded intentional cancellation and native close");
    }
}
