package com.familyconnect.app;

import android.content.Context;
import com.google.gson.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.CompletableFuture;

interface TunnelEngine { void up(String profile)throws Exception;void down()throws Exception; }

final class NativeRestricted {
    static final java.util.concurrent.CountDownLatch delivered=new java.util.concurrent.CountDownLatch(1),release=new java.util.concurrent.CountDownLatch(1);
    static volatile int begins;
    static volatile long provisioningBudget;
    static JsonObject call(String operation,Object... pairs){
        try{
            JsonObject request=new JsonObject();request.addProperty("operation",operation);
            for(int index=0;index<pairs.length;index+=2)request.add((String)pairs[index],new Gson().toJsonTree(pairs[index+1] instanceof byte[]?Base64.getEncoder().encodeToString((byte[])pairs[index+1]):pairs[index+1]));
            HttpURLConnection connection=(HttpURLConnection)new URL(System.getProperty("fixture.bridge")).openConnection();
            connection.setConnectTimeout(30000);connection.setReadTimeout(30000);connection.setDoOutput(true);connection.setRequestMethod("POST");
            try{try(OutputStream output=connection.getOutputStream()){output.write(request.toString().getBytes(StandardCharsets.UTF_8));}
                try(InputStream input=connection.getInputStream()){return JsonParser.parseString(new String(input.readAllBytes(),StandardCharsets.UTF_8)).getAsJsonObject();}
            }finally{connection.disconnect();}
        }catch(Exception error){throw new IllegalStateException("Native fixture RPC failed",error);}
    }
    static void load(){}
    static long provisionBegin(byte[] locator,byte[] anchor,String gateway,String resolver,long budget,Object protector){provisioningBudget=budget;return call("open","locator",locator,"anchor",anchor,"gateway",gateway).get("handle").getAsLong();}
    static String provisionPost(long handle,String path,String body,String id){JsonObject result=call("post","path",path,"body",body,"id",id);if(Boolean.getBoolean("fixture.late")&&path.equals("/friends/restricted-readiness")){delivered.countDown();try{if(!release.await(5,java.util.concurrent.TimeUnit.SECONDS))throw new AssertionError("Late response release");}catch(InterruptedException error){throw new AssertionError(error);}}return result.has("reply")?result.get("reply").toString():null;}
    static void provisionClose(long handle){call("close");}
    static int validationCode(byte[] raw,byte[] identity,byte[] anchor){return call("validate","raw",raw,"identity",identity,"anchor",anchor).get("code").getAsInt();}
    static boolean validateDelivery(byte[] raw,byte[] identity,byte[] anchor){return validationCode(raw,identity,anchor)==0;}
    static long beginReady(byte[] raw,byte[] identity,byte[] anchor,String resolver,long budget,android.net.VpnService service,int profile){begins++;return call("begin","raw",raw,"identity",identity,"anchor",anchor).get("handle").getAsLong();}
    static int state(long handle){return call("state").get("state").getAsInt();}
    static boolean attach(long handle,int descriptor){return call("attach").get("accepted").getAsBoolean();}
    static boolean stop(long handle){return call("stop").get("stopped").getAsBoolean();}
    static String stats(long handle){return call("stats").toString();}
    static long begin(String directory,String control,String resolver,long budget,android.net.VpnService protector){throw new AssertionError("Diagnostic provisioning forbidden");}
    static boolean renew(long handle,byte[] raw,byte[] identity){throw new AssertionError("No renewal in cold test");}
}
final class TcpVpnService extends android.net.VpnService {
    static final CompletableFuture<TcpVpnService> ready=CompletableFuture.completedFuture(new TcpVpnService());
    final CompletableFuture<Void> stopped=new CompletableFuture<>();Runnable revoked;
    void stopSelf(){stopped.complete(null);}
}
final class ChatNetworkAndroid {
    static int blocked;
    ChatNetworkAndroid(Context context){}
    String provisioningResolver(){return "127.0.0.1:53";}
    javax.net.ssl.HttpsURLConnection openHttps(String address,ReadinessFetchTrace trace)throws IOException{
        blocked++;
        if(!Boolean.getBoolean("fixture.blackhole"))throw new SocketTimeoutException("Isolated direct HTTPS disabled");
        return new javax.net.ssl.HttpsURLConnection(new URL(address)){
            public String getCipherSuite(){throw new AssertionError();}public java.security.cert.Certificate[] getLocalCertificates(){return null;}public java.security.cert.Certificate[] getServerCertificates(){throw new AssertionError();}
            public void disconnect(){}public boolean usingProxy(){return false;}public void connect(){throw new AssertionError();}
            public OutputStream getOutputStream()throws IOException{try{Thread.sleep(getReadTimeout());}catch(InterruptedException error){throw new java.io.InterruptedIOException();}throw new SocketTimeoutException("Isolated TLS/write blackhole");}
        };
    }
}
final class ControlRnsAndroid {
    static int blocked;
    ControlRnsAndroid(Context context,long deadline){}
    void openReadiness(ReadinessFetchTrace trace)throws FriendsReadinessProtocol.Unavailable{blocked++;if(Boolean.getBoolean("fixture.blackhole"))try{Thread.sleep(5000);}catch(InterruptedException error){throw new AssertionError(error);}throw new FriendsReadinessProtocol.Unavailable();}
    byte[] requestReadiness(String path,byte[] raw){throw new AssertionError("Direct RNS forbidden");}
    void cancel(){}void close(){}
}
final class ControlTrust {
    static byte[] anchor(Context context)throws IOException{return Base64.getDecoder().decode(Files.readString(Path.of(System.getProperty("fixture.assets"),"anchor.pub")).trim());}
}
final class ConnectionService { static String status="off",healthStatus="off"; }
final class BuildConfig { static String VERSION_NAME="source-cold-candidate";static int VERSION_CODE=113; }
final class SpeedProfile { static int read(Context context){return 0;} }
final class Diagnostics {
    static final java.util.concurrent.CountDownLatch refreshed=new java.util.concurrent.CountDownLatch(1);
    static String readinessConnection(Context context){return "isolated-owner";}
    static void readinessResult(Context context,ReadinessImportResult.Code code){}
    static void readinessFetch(Context context,ReadinessFetchTrace trace){refreshed.countDown();}
    static void readiness(Context context,boolean ready){}static void vpn(Context context,boolean active){}
    static void nativeStats(Context context,org.json.JSONObject snapshot){}static void cleanup(Context context,boolean stopped){}
}
final class StartupDiagnostics {
    static void begin(Context context,long handle){}static void stopped(Context context,long handle){}
    static void capture(Context context,long handle,org.json.JSONObject value){}
    static ConnectivityOrchestrator.Rejected rejected(long handle,ConnectivityOrchestrator.Failure reason){return new ConnectivityOrchestrator.Rejected(reason);}
}
final class FriendsConfigurationVault {
    FriendsConfigurationVault(Context context){}FriendsConfigurationVault(Context context,boolean explicit){}
    byte[] read(){throw new AssertionError();}void create(byte[] raw){throw new AssertionError();}void write(byte[] raw){throw new AssertionError();}
}
final class ChatCarrier implements AutoCloseable {
    ChatCarrier(Context context){}JsonObject request(String path,String body,int timeout){throw new AssertionError("No warm chat");}
    public void close(){}
}
final class DeviceSupport { static void store(Context context,String device,String support){throw new AssertionError();} }
final class ChatLocalAndroid {
    JsonElement call(String method,JsonObject args){throw new AssertionError();}
    JsonObject enrollmentProof(String device,String nonce){throw new AssertionError();}
}
